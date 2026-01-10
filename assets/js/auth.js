/**
 * Sitewide Authentication Module
 * Handles GitHub Personal Access Token (PAT) authentication
 * 
 * Security Note: This is a temporary implementation using PATs.
 * For production, implement OAuth2 with secure backend token exchange.
 * See KNOWN_ISSUES.md for authentication roadmap.
 * 
 * Global Variables Available After Init:
 * - window.authToken: Current GitHub PAT (or null)
 * - window.isContributor: Boolean flag for contributor status
 * - window.githubUsername: Authenticated GitHub username (or null)
 */

(function() {
    // Initialize globals
    window.authToken = null;
    window.isContributor = false;
    window.githubUsername = null;

    /**
     * Initialize authentication on page load
     * Loads saved token from localStorage and validates it
     */
    window.initAuth = async function() {
        const saved = localStorage.getItem('github_pat_token');
        if (saved) {
            window.authToken = saved;
            await checkGitHubAuth();
        } else {
            renderAuthUI();
        }
    };

    /**
     * Check if user is authenticated and is a contributor.
     * Uses GitHub Personal Access Token (stored in localStorage).
     */
    window.checkGitHubAuth = async function() {
        if (!window.authToken) {
            renderAuthUI();
            return false;
        }

        try {
            // Verify token and check if user is collaborator
            const userResponse = await fetch('https://api.github.com/user', {
                headers: {
                    'Authorization': `token ${window.authToken}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!userResponse.ok) {
                console.warn('Invalid GitHub token');
                localStorage.removeItem('github_pat_token');
                window.authToken = null;
                window.githubUsername = null;
                window.isContributor = false;
                renderAuthUI();
                return false;
            }

            const user = await userResponse.json();
            window.githubUsername = user.login;

            // Check if user is collaborator
            const collabResponse = await fetch('https://api.github.com/repos/scerruti/cph50-control/collaborators/' + user.login, {
                headers: {
                    'Authorization': `token ${window.authToken}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (collabResponse.ok) {
                window.isContributor = true;
                renderAuthUI(user.login, true);
                return true;
            } else {
                console.warn('User is not a collaborator');
                window.isContributor = false;
                renderAuthUI(user.login, false);
                return false;
            }
        } catch (e) {
            console.error('Auth check failed:', e);
            renderAuthUI();
            return false;
        }
    };

    /**
     * Render authentication UI based on auth state
     */
    window.renderAuthUI = function(username = null, isContrib = false) {
        const container = document.getElementById('auth-container');
        if (!container) {
            console.warn('auth-container element not found');
            return;
        }

        if (username && isContrib) {
            // Authenticated contributor
            container.innerHTML = `
                <div class="status-message" style="border-left-color: #10b981; background: #ecfdf5; color: #065f46;">
                    ✓ Logged in as <strong>${username}</strong> (contributor)
                    <button onclick="window.logoutGitHub()" style="margin-left: 20px; padding: 4px 12px; font-size: 12px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;">Logout</button>
                </div>
            `;
        } else if (username) {
            // Authenticated but not contributor
            container.innerHTML = `
                <div class="status-message warning">
                    Logged in as <strong>${username}</strong> (read-only access)
                    <button onclick="window.logoutGitHub()" style="margin-left: 20px; padding: 4px 12px; font-size: 12px; background: #6b7280; color: white; border: none; border-radius: 4px; cursor: pointer;">Logout</button>
                </div>
            `;
        } else {
            // Not authenticated
            container.innerHTML = `
                <div class="status-message" style="border-left-color: #6366f1; background: #eef2ff; color: #312e81;">
                    <details>
                        <summary style="cursor: pointer; font-weight: 600;">GitHub Login (Contributors Only)</summary>
                        <div style="margin-top: 12px;">
                            <p style="font-size: 12px; margin: 0 0 10px 0;">Paste your GitHub Personal Access Token (repo scope):</p>
                            <div style="display: flex; gap: 8px;">
                                <input type="password" id="pat-input" placeholder="ghp_..." style="flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                                <button onclick="window.loginWithPAT()" style="padding: 8px 16px; background: #6366f1; color: white; border: none; border-radius: 4px; cursor: pointer;">Login</button>
                            </div>
                            <p style="font-size: 11px; color: #666; margin-top: 8px;">
                                <a href="https://github.com/settings/tokens" target="_blank">Create a token</a> with <code>repo</code> scope
                            </p>
                        </div>
                    </details>
                </div>
            `;
        }
    };

    /**
     * Store PAT and verify access
     */
    window.loginWithPAT = function() {
        const input = document.getElementById('pat-input');
        if (!input) return;

        const token = input.value.trim();
        if (!token) {
            alert('Please paste a GitHub Personal Access Token');
            return;
        }

        localStorage.setItem('github_pat_token', token);
        window.authToken = token;
        window.checkGitHubAuth();
    };

    /**
     * Clear authentication
     */
    window.logoutGitHub = function() {
        localStorage.removeItem('github_pat_token');
        window.authToken = null;
        window.githubUsername = null;
        window.isContributor = false;
        window.renderAuthUI();
    };
})();
