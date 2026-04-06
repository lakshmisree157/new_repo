import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import firebaseConfig from './firebase-config.js';

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export async function handleGoogleLogin(messageEl, targetRole) {
    messageEl.className = 'message';
    try {
        const result = await signInWithPopup(auth, provider);
        const idToken = await result.user.getIdToken();

        // Call backend firebase-login
        const response = await fetch('/api/auth/firebase-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
        });

        const data = await response.json();

        if (data.needs_registration) {
            // Redirect to complete profile
            sessionStorage.setItem('firebase_id_token', idToken);
            sessionStorage.setItem('firebase_email', data.email);
            window.location.href = '/complete-profile.html';
        } else if (data.access_token) {
            if (targetRole && data.user.role !== targetRole) {
                messageEl.className = 'message error';
                messageEl.textContent = `✗ Access denied: User is registered as ${data.user.role}, not ${targetRole}.`;
                return;
            }
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            messageEl.className = 'message success';
            messageEl.textContent = '✓ Login successful! Redirecting...';
            setTimeout(() => {
                window.location.href = data.user.role === 'adopter' ? '/adopter-dashboard.html' : '/center-dashboard.html';
            }, 1000);
        } else {
            messageEl.className = 'message error';
            messageEl.textContent = '✗ Firebase login failed: ' + (data.error || 'Unknown error');
        }
    } catch (error) {
        console.error(error);
        messageEl.className = 'message error';
        messageEl.textContent = '✗ Google Sign-in failed';
    }
}
