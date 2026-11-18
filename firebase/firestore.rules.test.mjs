import { readFile } from "node:fs/promises";
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import {
  initializeTestEnvironment,
  assertSucceeds,
  assertFails
} from "@firebase/rules-unit-testing";
import {
  doc, getDoc, getDocs, collection, setDoc, deleteDoc,
  writeBatch, serverTimestamp
} from "firebase/firestore";

const projectId = "demo-earth-unlock";
let env;

before(async () => {
  env = await initializeTestEnvironment({
    projectId,
    firestore: {
      rules: await readFile(new URL("./firestore.rules", import.meta.url), "utf8")
    }
  });
});

after(async () => {
  await env.cleanup();
});

function profile(nickname = "ExplorerOne", normalized = "explorerone") {
  return {
    nickname,
    nicknameNormalized: normalized,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    recoveryProvider: "none"
  };
}

async function createAccount(uid, nickname = "ExplorerOne", normalized = "explorerone") {
  const db = env.authenticatedContext(uid).firestore();
  const batch = writeBatch(db);
  batch.set(doc(db, "profiles", uid), profile(nickname, normalized));
  batch.set(doc(db, "nickname_claims", normalized), {
    uid,
    createdAt: serverTimestamp()
  });
  await assertSucceeds(batch.commit());
  return db;
}

test("profile and nickname claim can be committed in one atomic batch", async () => {
  await createAccount("alice");
});

test("profiles are private and cannot be listed", async () => {
  const owner = await createAccount("alice");
  const stranger = env.authenticatedContext("bob").firestore();
  await assertSucceeds(getDoc(doc(owner, "profiles", "alice")));
  await assertFails(getDoc(doc(stranger, "profiles", "alice")));
  await assertFails(getDocs(collection(owner, "profiles")));
});

test("nickname claims allow exact checks but deny enumeration and duplicates", async () => {
  const alice = await createAccount("alice");
  const bob = env.authenticatedContext("bob").firestore();
  await assertSucceeds(getDoc(doc(bob, "nickname_claims", "explorerone")));
  await assertFails(getDocs(collection(bob, "nickname_claims")));
  const batch = writeBatch(bob);
  batch.set(doc(bob, "profiles", "bob"), profile("ExplorerOne", "explorerone"));
  batch.set(doc(bob, "nickname_claims", "explorerone"), {
    uid: "bob",
    createdAt: serverTimestamp()
  });
  await assertFails(batch.commit());
  await assertSucceeds(getDoc(doc(alice, "profiles", "alice")));
});

test("nickname change releases the old claim only in the same atomic batch", async () => {
  const db = await createAccount("alice");
  const batch = writeBatch(db);
  batch.update(doc(db, "profiles", "alice"), {
    nickname: "NewExplorer",
    nicknameNormalized: "newexplorer",
    updatedAt: serverTimestamp()
  });
  batch.set(doc(db, "nickname_claims", "newexplorer"), {
    uid: "alice",
    createdAt: serverTimestamp()
  });
  batch.delete(doc(db, "nickname_claims", "explorerone"));
  await assertSucceeds(batch.commit());
});

test("leaderboard is public but writes are restricted to the owner and valid scores", async () => {
  const owner = env.authenticatedContext("alice").firestore();
  const stranger = env.authenticatedContext("bob").firestore();
  const row = {
    nickname: "ExplorerOne",
    exploredAreaM2: 1200,
    exploredCellCount: 48,
    updatedAt: serverTimestamp()
  };
  await assertSucceeds(setDoc(doc(owner, "leaderboard", "alice"), row));
  await assertSucceeds(getDoc(doc(stranger, "leaderboard", "alice")));
  await assertFails(setDoc(doc(stranger, "leaderboard", "alice"), row));
  await assertFails(setDoc(doc(owner, "leaderboard", "alice"), {
    ...row, exploredCellCount: -1
  }));
  await assertFails(setDoc(doc(owner, "leaderboard", "alice"), {
    ...row, privateEmail: "not-allowed@example.com"
  }));
});

test("backup chunks are private and validate payload shape and size", async () => {
  const owner = env.authenticatedContext("alice").firestore();
  const stranger = env.authenticatedContext("bob").firestore();
  const ref = doc(owner, "exploration_backups", "alice", "chunks", "chunk-0001");
  await assertSucceeds(setDoc(ref, {
    formatVersion: 1,
    payload: "compressed-cell-data",
    updatedAt: serverTimestamp()
  }));
  await assertSucceeds(getDoc(ref));
  await assertFails(getDoc(doc(stranger, "exploration_backups", "alice", "chunks", "chunk-0001")));
  await assertFails(setDoc(doc(owner, "exploration_backups", "alice", "chunks", "bad"), {
    formatVersion: 1,
    payload: "x".repeat(700001),
    updatedAt: serverTimestamp()
  }));
  await assertFails(setDoc(doc(stranger, "exploration_backups", "alice", "chunks", "chunk-0002"), {
    formatVersion: 1,
    payload: "forged",
    updatedAt: serverTimestamp()
  }));
  await assertSucceeds(deleteDoc(ref));
});
