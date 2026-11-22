/**
 * ApnaStay - Main JavaScript Interactions
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Setup CSRF Token Helper for AJAX
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // 2. Wishlist Heart Button AJAX Toggle
    const wishlistButtons = document.querySelectorAll('.wishlist-toggle-btn');
    wishlistButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const listingId = this.getAttribute('data-listing-id');
            const heartIcon = this.querySelector('i');
            const url = `/wishlist/toggle/${listingId}/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                }
            })
            .then(res => {
                if (res.status === 403 || res.redirected) {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return;
                }
                return res.json();
            })
            .then(data => {
                if (data && data.success) {
                    if (data.is_added) {
                        this.classList.add('active');
                        heartIcon.classList.remove('bi-heart');
                        heartIcon.classList.add('bi-heart-fill');
                    } else {
                        this.classList.remove('active');
                        heartIcon.classList.remove('bi-heart-fill');
                        heartIcon.classList.add('bi-heart');
                    }
                    // Update navbar badge if present
                    const badge = document.getElementById('navbar-wishlist-count');
                    if (badge) {
                        badge.textContent = data.wishlist_count;
                        badge.style.display = data.wishlist_count > 0 ? 'inline-block' : 'none';
                    }
                }
            })
            .catch(err => console.error('Error toggling wishlist:', err));
        });
    });

    // 3. Dynamic Price Calculation for Booking Widget
    const checkInInput = document.getElementById('booking_check_in');
    const checkOutInput = document.getElementById('booking_check_out');
    const listingSlug = document.getElementById('booking-widget-container')?.getAttribute('data-slug');

    function updatePriceBreakdown() {
        if (!checkInInput || !checkOutInput || !listingSlug) return;

        const checkInVal = checkInInput.value;
        const checkOutVal = checkOutInput.value;

        if (!checkInVal || !checkOutVal) return;

        const apiUrl = `/bookings/api/calculate/${listingSlug}/?check_in=${checkInVal}&check_out=${checkOutVal}`;

        fetch(apiUrl)
            .then(res => res.json())
            .then(data => {
                const breakdownContainer = document.getElementById('live-price-breakdown');
                const bookSubmitBtn = document.getElementById('book-submit-btn');

                if (data.error) {
                    if (breakdownContainer) breakdownContainer.innerHTML = `<div class="text-danger small my-2">${data.error}</div>`;
                    if (bookSubmitBtn) bookSubmitBtn.disabled = true;
                } else {
                    if (breakdownContainer) {
                        breakdownContainer.innerHTML = `
                            <div class="price-breakdown-row">
                                <span>₹${Number(data.price_per_night).toLocaleString('en-IN')} × ${data.nights} night${data.nights > 1 ? 's' : ''}</span>
                                <span>₹${Number(data.subtotal).toLocaleString('en-IN')}</span>
                            </div>
                            ${data.cleaning_fee > 0 ? `
                            <div class="price-breakdown-row">
                                <span>Cleaning fee</span>
                                <span>₹${Number(data.cleaning_fee).toLocaleString('en-IN')}</span>
                            </div>` : ''}
                            <div class="price-breakdown-row">
                                <span>ApnaStay service fee (5%)</span>
                                <span>₹${Number(data.service_fee).toLocaleString('en-IN')}</span>
                            </div>
                            <div class="price-breakdown-total">
                                <span>Total Amount (INR)</span>
                                <span>₹${Number(data.total_amount).toLocaleString('en-IN')}</span>
                            </div>
                        `;
                    }
                    if (bookSubmitBtn) {
                        if (!data.is_available) {
                            bookSubmitBtn.disabled = true;
                            bookSubmitBtn.textContent = 'Dates Not Available';
                            bookSubmitBtn.classList.replace('btn-coral', 'btn-secondary');
                        } else {
                            bookSubmitBtn.disabled = false;
                            bookSubmitBtn.textContent = 'Reserve Now';
                            bookSubmitBtn.classList.replace('btn-secondary', 'btn-coral');
                        }
                    }
                }
            })
            .catch(err => console.error('Price calculation error:', err));
    }

    if (checkInInput && checkOutInput) {
        checkInInput.addEventListener('change', function () {
            // Set min checkout to 1 day after checkin
            if (this.value) {
                const nextDay = new Date(this.value);
                nextDay.setDate(nextDay.getDate() + 1);
                checkOutInput.min = nextDay.toISOString().split('T')[0];
                if (checkOutInput.value && checkOutInput.value <= this.value) {
                    checkOutInput.value = nextDay.toISOString().split('T')[0];
                }
            }
            updatePriceBreakdown();
        });

        checkOutInput.addEventListener('change', updatePriceBreakdown);

        // Run initial calculation if dates present
        if (checkInInput.value && checkOutInput.value) {
            updatePriceBreakdown();
        }
    }

    // 4. Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 6000);
    });

    // 5. Image Preview for Multiple Upload Form
    const imageInput = document.getElementById('id_images');
    const previewContainer = document.getElementById('image-previews-container');
    if (imageInput && previewContainer) {
        imageInput.addEventListener('change', function () {
            previewContainer.innerHTML = '';
            if (this.files) {
                Array.from(this.files).forEach((file, index) => {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        const col = document.createElement('div');
                        col.className = 'col-6 col-md-3 mb-2';
                        col.innerHTML = `
                            <div class="border rounded p-1 position-relative">
                                <img src="${e.target.result}" class="img-fluid rounded" style="height: 110px; width:100%; object-fit: cover;">
                                ${index === 0 ? '<span class="badge bg-danger position-absolute top-0 start-0 m-2">Cover</span>' : ''}
                            </div>
                        `;
                        previewContainer.appendChild(col);
                    };
                    reader.readAsDataURL(file);
                });
            }
        });
    }
});
