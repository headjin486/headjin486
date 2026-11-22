import { readFile } from "node:fs/promises";
import test from "node:test";
import assert from "node:assert/strict";
import { initializeTestEnvironment } from "@firebase/rules-unit-testing";
import { initializeApp, deleteApp } from "firebase/app";
import {
  getAuth, connectAuthEmulator, signInAnonymously,
  createUserWithEmailAndPassword
} from "firebase/auth";
import {
  collection, doc, getDocs, setDoc, writeBatch
} from "firebase/firestore";

const projectId = "demo-earth-unlock";
const config = { apiKey: "demo-api-key", authDomain: "localhost", projectId };

function makeAuthClient(name) {
  const app = initializeApp(config, name);
  const auth = getAuth(app);
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
  return { app, auth };
}

// Firestore test contexts carry the exact UID created in the Auth emulator.
// The separate rules suite verifies that only this UID can access its own backup.
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

async function runDeletionScenario(name, createTarget) {
  const env = await initializeTestEnvironment({
    projectId,
    firestore: { rules: await readFile(new URL("./firestore.rules", import.meta.url), "utf8") }
  });
  const target = makeAuthClient(`${name}-target`);
  const other = makeAuthClient(`${name}-other`);
  try {
    const targetCredential = await createTarget(target.auth);
    const otherCredential = await signInAnonymously(other.auth);
    const targetUid = targetCredential.user.uid;
    const otherUid = otherCredential.user.uid;
    const targetDb = env.authenticatedContext(targetUid).firestore();
    const otherDb = env.authenticatedContext(otherUid).firestore();

    await seedChunks(targetDb, targetUid, "target");
    await seedChunks(otherDb, otherUid, "other");

    await deleteAccountAndBackups(target.auth, targetDb);
    assert.equal(target.auth.currentUser, null, "deleted Auth user must be signed out");

    const targetRemaining = await getDocs(collection(targetDb, "exploration_backups", targetUid, "chunks"));
    assert.equal(targetRemaining.size, 0, "all target backup chunks must be deleted");
    const otherRemaining = await getDocs(collection(otherDb, "exploration_backups", otherUid, "chunks"));
    assert.equal(otherRemaining.size, 3, "another UID's backup must remain untouched");
  } finally {
    await env.cleanup();
    await deleteApp(target.app);
    await deleteApp(other.app);
  }
}

test("anonymous Firebase account deletion removes its chunks and preserves another UID", async () => {
  await runDeletionScenario("anonymous", auth => signInAnonymously(auth));
});

test("email/password Firebase account deletion removes its chunks and preserves another UID", async () => {
  await runDeletionScenario("password", auth => {
    const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return createUserWithEmailAndPassword(auth, `delete-test-${suffix}@example.test`, "Test-password-123!");
  });
});
