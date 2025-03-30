document.addEventListener('DOMContentLoaded', function () {
    // Add any additional event listeners or validation logic here
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    if (passwordInput && confirmPasswordInput) {
        passwordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);
    }

    function validatePassword() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Password requirements
        const hasLength = password.length >= 8;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasDigit = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*]/.test(password);

        // Update requirement indicators
        document.getElementById('length').classList.toggle('valid', hasLength);
        document.getElementById('uppercase').classList.toggle('valid', hasUppercase);
        document.getElementById('lowercase').classList.toggle('valid', hasLowercase);
        document.getElementById('digit').classList.toggle('valid', hasDigit);
        document.getElementById('special').classList.toggle('valid', hasSpecial);

        // Check if passwords match
        if (password !== confirmPassword) {
            alert('Passwords do not match.');
            return false;
        }

        return true;
    }
});