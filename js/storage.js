// Saves progress + settings to this browser, and to Firebase when it's configured and you're signed in.
import { firebaseConfig } from './firebase-config.js';

const LS_KEY = 'livingdex-v1';
const FB = 'https://www.gstatic.com/firebasejs/10.12.2/';

let state = { progress: {}, settings: {}, updated: 0 };
let fb = null;          // { auth, db, fs, user }
let saveTimer = null;
let onRemote = () => {};
let onAuth = () => {};

function readLocal() {
  try { const raw = localStorage.getItem(LS_KEY); if (raw) return JSON.parse(raw); } catch (e) { /* ignore */ }
  return null;
}
function writeLocal() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
}

export function load() {
  const local = readLocal();
  if (local) state = { progress: local.progress || {}, settings: local.settings || {}, updated: local.updated || 0 };
  return state;
}
export function get() { return state; }

export function save() {
  state.updated = Date.now();
  writeLocal();
  clearTimeout(saveTimer);
  saveTimer = setTimeout(pushRemote, 1200);
}

async function pushRemote() {
  if (!fb || !fb.user) return;
  const { doc, setDoc } = fb.fs;
  try {
    await setDoc(doc(fb.db, 'users', fb.user.uid), { progress: state.progress, settings: state.settings, updated: state.updated });
  } catch (e) { console.error('Cloud save failed', e); }
}

export function cloudEnabled() { return !!firebaseConfig; }
export function user() { return fb && fb.user; }

export async function initCloud(handlers) {
  onRemote = handlers.onRemote || onRemote;
  onAuth = handlers.onAuth || onAuth;
  if (!firebaseConfig) { onAuth(null); return; }
  const [{ initializeApp }, authMod, fs] = await Promise.all([
    import(FB + 'firebase-app.js'), import(FB + 'firebase-auth.js'), import(FB + 'firebase-firestore.js'),
  ]);
  const app = initializeApp(firebaseConfig);
  const auth = authMod.getAuth(app);
  const db = fs.getFirestore(app);
  fb = { auth, db, fs, authMod, user: null };
  authMod.onAuthStateChanged(auth, async (u) => {
    fb.user = u;
    onAuth(u);
    if (!u) return;
    const snap = await fs.getDoc(fs.doc(db, 'users', u.uid));
    if (snap.exists()) {
      const remote = snap.data();
      if ((remote.updated || 0) >= (state.updated || 0)) {
        state = { progress: remote.progress || {}, settings: remote.settings || {}, updated: remote.updated || 0 };
        writeLocal();
        onRemote(state);
      } else {
        pushRemote();
      }
    } else {
      pushRemote();
    }
  });
}

export async function signIn() {
  if (!fb) return;
  const p = new fb.authMod.GoogleAuthProvider();
  try { await fb.authMod.signInWithPopup(fb.auth, p); }
  catch (e) { await fb.authMod.signInWithRedirect(fb.auth, p); }
}
export async function signOut() { if (fb) await fb.authMod.signOut(fb.auth); }

export function exportJSON() {
  const blob = new Blob([JSON.stringify({ app: 'livingdex', version: 1, ...state }, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `livingdex-backup-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export function importJSON(text) {
  const data = JSON.parse(text);
  if (data.app !== 'livingdex' || typeof data.progress !== 'object') throw new Error('Not a Living Dex backup file');
  state = { progress: data.progress || {}, settings: data.settings || {}, updated: Date.now() };
  writeLocal();
  pushRemote();
  return state;
}
