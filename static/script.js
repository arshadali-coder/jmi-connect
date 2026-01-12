// JMIConnect Global Utilities

async function logout() {
    if (!confirm('Are you sure you want to log out?')) return;
    try {
        const response = await fetch('/auth/logout');
        if (response.ok) {
            window.location.href = '/';
        } else {
            alert('Logout failed');
        }
    } catch (error) {
        console.error('Error:', error);
        window.location.href = '/';
    }
}
