// subscription.js - Handles subscription flow and Stripe integration

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Stripe
    const stripe = Stripe(window.stripePublishableKey);
    const elements = stripe.elements();
    const card = elements.create('card');

    // Get DOM elements
    const subscribeBtn = document.getElementById('subscribeBtn');
    const subscribeModal = document.getElementById('subscribeModal');
    const paymentModal = document.getElementById('paymentModal');
    const closeSubscribeModal = document.getElementById('closeSubscribeModal');
    const closePaymentModal = document.getElementById('closePaymentModal');
    const paymentForm = document.getElementById('payment-form');
    const cardElement = document.getElementById('card-element');
    const cardErrors = document.getElementById('card-errors');
    const submitButton = document.getElementById('submit-payment');
    const spinner = document.getElementById('spinner');
    const buttonText = document.getElementById('button-text');

    // Mount card element
    if (cardElement) {
        card.mount('#card-element');
    }

    // Show subscription modal when subscribe button is clicked
    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', function() {
            if (!window.isAuthenticated) {
                window.location.href = '/login/';
                return;
            }

            if (!window.isKycCompleted) {
                window.location.href = '/kyc/';
                return;
            }

            subscribeModal.style.display = 'block';
        });
    }

    // Close modals when clicking close button or outside
    if (closeSubscribeModal) {
        closeSubscribeModal.onclick = function() {
            subscribeModal.style.display = 'none';
        };
    }

    if (closePaymentModal) {
        closePaymentModal.onclick = function() {
            paymentModal.style.display = 'none';
        };
    }

    window.onclick = function(event) {
        if (event.target == subscribeModal) {
            subscribeModal.style.display = 'none';
        }
        if (event.target == paymentModal) {
            paymentModal.style.display = 'none';
        }
    };

    // Handle tier selection
    document.querySelectorAll('.tier-card .subscribe-btn').forEach(button => {
        button.addEventListener('click', function() {
            const tierId = this.dataset.tierId;
            const username = subscribeBtn.dataset.username;
            
            // Hide subscription modal and show payment modal
            subscribeModal.style.display = 'none';
            paymentModal.style.display = 'block';
            
            // Store selected tier ID for payment processing
            paymentForm.dataset.tierId = tierId;
            paymentForm.dataset.username = username;
        });
    });

    // Handle payment submission
    if (paymentForm) {
        paymentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const tierId = this.dataset.tierId;
            const username = this.dataset.username;

            setLoading(true);

            try {
                const { paymentMethod, error } = await stripe.createPaymentMethod({
                    type: 'card',
                    card: card,
                });

                if (error) {
                    showError(error.message);
                    return;
                }

                // Create subscription
                const response = await fetch(`/tipster/subscribe/${username}/${tierId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        payment_method_id: paymentMethod.id,
                    }),
                });

                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                const { client_secret } = data;
                const result = await stripe.confirmCardPayment(client_secret);

                if (result.error) {
                    showError(result.error.message);
                } else {
                    // Payment successful
                    paymentModal.style.display = 'none';
                    subscribeBtn.textContent = 'Subscribed';
                    subscribeBtn.classList.add('subscribed');
                    subscribeBtn.disabled = true;
                    
                    // Show success message
                    showMessage('Successfully subscribed! Refreshing page...', 'success');
                    setTimeout(() => window.location.reload(), 2000);
                }
            } catch (error) {
                showError('An error occurred. Please try again.');
            }

            setLoading(false);
        });
    }

    // Helper functions
    function setLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            spinner.classList.remove('hidden');
            buttonText.textContent = 'Processing...';
        } else {
            submitButton.disabled = false;
            spinner.classList.add('hidden');
            buttonText.textContent = 'Subscribe Now';
        }
    }

    function showError(message) {
        const errorDiv = document.getElementById('card-errors');
        errorDiv.textContent = message;
        setLoading(false);
    }

    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.textContent = message;
        document.body.appendChild(messageDiv);
        setTimeout(() => messageDiv.remove(), 3000);
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}); 