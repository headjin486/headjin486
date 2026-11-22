import { readFile } from "node:fs/promises";
import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import { initializeTestEnvironment, assertSucceeds, assertFails } from "@firebase/rules-unit-testing";
import { doc, getDoc, getDocs, collection, setDoc, deleteDoc, serverTimestamp } from "firebase/firestore";

const projectId = "demo-earth-unlock";
let env;

before(async () => {
  env = await initializeTestEnvironment({
    projectId,
    firestore: { rules: await readFile(new URL("./firestore.rules", import.meta.url), "utf8") }
  });
});
after(async () => { await env.cleanup(); });

test("backup chunks are private to the authenticated owner", async () => {
  const owner = env.authenticatedContext("alice").firestore();
  const stranger = env.authenticatedContext("bob").firestore();
  const ref = doc(owner, "exploration_backups", "alice", "chunks", "chunk-0001");
  await assertSucceeds(setDoc(ref, { formatVersion: 1, payload: "compressed-cell-data", updatedAt: serverTimestamp() }));
  await assertSucceeds(getDoc(ref));
  await assertFails(getDoc(doc(stranger, "exploration_backups", "alice", "chunks", "chunk-0001")));
  await assertFails(getDocs(collection(stranger, "exploration_backups", "alice", "chunks")));
  await assertFails(setDoc(doc(owner, "exploration_backups", "alice", "chunks", "bad"), {
    formatVersion: 1, payload: "x".repeat(700001), updatedAt: serverTimestamp()
  }));
  await assertFails(setDoc(doc(stranger, "exploration_backups", "alice", "chunks", "chunk-0002"), {
    formatVersion: 1, payload: "forged", updatedAt: serverTimestamp()
  }));
  await assertSucceeds(deleteDoc(ref));
});

test("timestamp-only backup status marker is writable and private to its owner", async () => {
  const owner = env.authenticatedContext("alice").firestore();
  const stranger = env.authenticatedContext("bob").firestore();
  const marker = doc(owner, "exploration_backups", "alice", "chunks", "_backup_status");
  await assertSucceeds(setDoc(marker, { kind: "backup_status", updatedAt: serverTimestamp() }));
  await assertSucceeds(getDoc(marker));
  await assertFails(getDoc(doc(stranger, "exploration_backups", "alice", "chunks", "_backup_status")));
  await assertFails(setDoc(doc(owner, "exploration_backups", "alice", "chunks", "_backup_status"), {
    kind: "backup_status", updatedAt: serverTimestamp(), payload: "unexpected"
  }));
  await assertFails(setDoc(doc(owner, "exploration_backups", "alice", "chunks", "_backup_status"), {
    kind: "wrong_kind", updatedAt: serverTimestamp()
  }));
});

test("unauthenticated users cannot read or write backups", async () => {
  const db = env.unauthenticatedContext().firestore();
  const ref = doc(db, "exploration_backups", "alice", "chunks", "chunk-0001");
  await assertFails(getDoc(ref));
  await assertFails(setDoc(ref, { formatVersion: 1, payload: "data", updatedAt: serverTimestamp() }));
  await assertFails(setDoc(doc(db, "exploration_backups", "alice", "chunks", "_backup_status"), {
    kind: "backup_status", updatedAt: serverTimestamp()
  }));
});

test("backup schema rejects unsupported versions and unexpected fields", async () => {
  const db = env.authenticatedContext("alice").firestore();
  await assertFails(setDoc(doc(db, "exploration_backups", "alice", "chunks", "v2"), {
    formatVersion: 2, payload: "data", updatedAt: serverTimestamp()
  }));
  await assertFails(setDoc(doc(db, "exploration_backups", "alice", "chunks", "extra"), {
    formatVersion: 1, payload: "data", updatedAt: serverTimestamp(), rawGps: [36.5, 127.8]
  }));
});
