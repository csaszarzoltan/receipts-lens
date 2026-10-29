/**
 * Offline capture queue. Receipt photos taken without a connection are kept in IndexedDB
 * until the page can upload them.
 */

const DB_NAME = "receiptlens-offline";
const STORE = "captures";

export type PendingCapture = {
  id: string;
  name: string;
  type: string;
  blob: Blob;
  createdAt: string;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("IndexedDB is not available in this browser"));
      return;
    }
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE, { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("Could not open the offline queue"));
  });
}

function run<T>(mode: IDBTransactionMode, work: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const tx = db.transaction(STORE, mode);
        const request = work(tx.objectStore(STORE));
        tx.oncomplete = () => {
          db.close();
          resolve(request.result);
        };
        tx.onerror = () => {
          db.close();
          reject(tx.error ?? new Error("Offline queue transaction failed"));
        };
      }),
  );
}

export async function queueCapture(file: File): Promise<PendingCapture> {
  const entry: PendingCapture = {
    id: typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name: file.name,
    type: file.type,
    blob: file,
    createdAt: new Date().toISOString(),
  };
  await run("readwrite", (store) => store.put(entry));
  return entry;
}

export async function listQueued(): Promise<PendingCapture[]> {
  const rows = await run<PendingCapture[]>("readonly", (store) => store.getAll());
  return rows.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export async function removeQueued(id: string): Promise<void> {
  await run("readwrite", (store) => store.delete(id));
}
