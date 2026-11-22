import test from "node:test";
import assert from "node:assert/strict";
import { initializeApp, deleteApp } from "firebase/app";
import {
  getAuth, connectAuthEmulator, signInAnonymously,
  createUserWithEmailAndPassword
} from "firebase/auth";
import {
  getFirestore, connectFirestoreEmulator, collection, doc,
  getDocs, setDoc, writeBatch
} from "firebase/firestore";

const projectId = "demo-earth-unlock";
const config = { apiKey: "demo-api-key", authDomain: "localhost", projectId };

function makeClient(name) {
  const app = initializeApp(config, name);
  const auth = getAuth(app);
  const db = getFirestore(app);
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
  connectFirestoreEmulator(db, "127.0.0.1", 8080);
  return { app, auth, db };
}

// Mirrors the app's required ordering: remove every backup chunk, then delete Auth user.
async function deleteAccountAndBackups(auth, db) {
  const user = auth.currentUser;
  assert.ok(user, "test account must be signed in");
  const chunks = collection(db, "exploration_backups", user.uid, "chunks");
  const snapshot = await getDocs(chunks);
  for (let offset = 0; offset < snapshot.docs.length; offset += 400) {
    const batch = writeBatch(db);
    snapshot.docs.slice(offset, offset + 400).forEach(item => batch.delete(item.ref));
    await batch.commit();
  }
  await user.delete();
}

async function seedChunks(db, uid, prefix) {
  for (let i = 0; i < 3; i += 1) {
    await setDoc(doc(db, "exploration_backups", uid, "chunks", `${prefix}-${i}`), {
      formatVersion: 1,
      payload: `test-grid-payload-${i}`,
      updatedAt: new Date()
    });
  }
}

async function assertTargetRemovedAndOtherUserPreserved(target, other) {
  const remaining = await getDocs(collection(target.db, "exploration_backups", target.uid, "chunks"));
  assert.equal(remaining.size, 0, "all target backup chunks must be deleted");
  const otherRemaining = await getDocs(collection(other.db, "exploration_backups", other.uid, "chunks"));
  assert.equal(otherRemaining.size, 3, "another UID's backup must remain untouched");
}

test("anonymous Firebase account deletion removes its chunks and preserves another UID", async () => {
  const target = makeClient("anonymous-target");
  const other = makeClient("anonymous-other");
  try {
    const targetCredential = await signInAnonymously(target.auth);
    const otherCredential = await signInAnonymously(other.auth);
    target.uid = targetCredential.user.uid;
    other.uid = otherCredential.user.uid;
    await seedChunks(target.db, target.uid, "target");
    await seedChunks(other.db, other.uid, "other");

    await deleteAccountAndBackups(target.auth, target.db);
    assert.equal(target.auth.currentUser, null, "deleted anonymous Auth user must be signed out");
    await assertTargetRemovedAndOtherUserPreserved(target, other);
  } finally {
    await deleteApp(target.app);
    await deleteApp(other.app);
  }
});

test("email/password Firebase account deletion removes its chunks and preserves another UID", async () => {
  const target = makeClient("password-target");
  const other = makeClient("password-other");
  try {
    const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const targetCredential = await createUserWithEmailAndPassword(
      target.auth, `delete-test-${suffix}@example.test`, "Test-password-123!"
    );
    const otherCredential = await signInAnonymously(other.auth);
    target.uid = targetCredential.user.uid;
    other.uid = otherCredential.user.uid;
    await seedChunks(target.db, target.uid, "target");
    await seedChunks(other.db, other.uid, "other");

    await deleteAccountAndBackups(target.auth, target.db);
    assert.equal(target.auth.currentUser, null, "deleted Auth user must be signed out");
    await assertTargetRemovedAndOtherUserPreserved(target, other);
  } finally {
    await deleteApp(target.app);
    await deleteApp(other.app);
  }
});
