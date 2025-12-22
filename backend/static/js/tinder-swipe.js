/**
 * TinderSwipe - Tinder-style card swipe handler
 * Handles touch/mouse drag gestures with visual feedback
 */
class TinderSwipe {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            threshold: 100,           // Minimum distance to trigger swipe
            rotationFactor: 0.1,      // How much cards rotate during drag
            maxRotation: 30,          // Maximum rotation angle
            velocityThreshold: 0.5,   // Minimum velocity for quick flicks
            ...options
        };

        this.cards = [];
        this.currentIndex = 0;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.velocityX = 0;
        this.velocityY = 0;
        this.lastTime = 0;
        this.lastX = 0;
        this.lastY = 0;

        this.init();
    }

    init() {
        this.cardStack = this.container.querySelector('.swipe-card-stack');
        if (!this.cardStack) return;

        this.updateCards();
        this.attachEventListeners();
    }

    updateCards() {
        this.cards = Array.from(this.cardStack.querySelectorAll('.swipe-card'));
        this.updateCardPositions();
    }

    updateCardPositions() {
        this.cards.forEach((card, index) => {
            const relativeIndex = index - this.currentIndex;
            card.classList.remove('active', 'next-1', 'next-2', 'hidden');

            if (relativeIndex === 0) {
                card.classList.add('active');
            } else if (relativeIndex === 1) {
                card.classList.add('next-1');
            } else if (relativeIndex === 2) {
                card.classList.add('next-2');
            } else {
                card.classList.add('hidden');
            }
        });
    }

    attachEventListeners() {
        // Touch events
        this.cardStack.addEventListener('touchstart', (e) => this.onDragStart(e), { passive: false });
        this.cardStack.addEventListener('touchmove', (e) => this.onDragMove(e), { passive: false });
        this.cardStack.addEventListener('touchend', (e) => this.onDragEnd(e));
        this.cardStack.addEventListener('touchcancel', (e) => this.onDragEnd(e));

        // Mouse events
        this.cardStack.addEventListener('mousedown', (e) => this.onDragStart(e));
        document.addEventListener('mousemove', (e) => this.onDragMove(e));
        document.addEventListener('mouseup', (e) => this.onDragEnd(e));
    }

    getActiveCard() {
        return this.cards[this.currentIndex];
    }

    onDragStart(e) {
        const card = this.getActiveCard();
        if (!card) return;

        this.isDragging = true;
        card.classList.add('dragging');

        const point = e.touches ? e.touches[0] : e;
        this.startX = point.clientX;
        this.startY = point.clientY;
        this.currentX = 0;
        this.currentY = 0;
        this.lastX = point.clientX;
        this.lastY = point.clientY;
        this.lastTime = Date.now();
        this.velocityX = 0;
        this.velocityY = 0;

        if (e.cancelable) e.preventDefault();
    }

    onDragMove(e) {
        if (!this.isDragging) return;

        const card = this.getActiveCard();
        if (!card) return;

        const point = e.touches ? e.touches[0] : e;
        this.currentX = point.clientX - this.startX;
        this.currentY = point.clientY - this.startY;

        // Calculate velocity
        const now = Date.now();
        const dt = now - this.lastTime;
        if (dt > 0) {
            this.velocityX = (point.clientX - this.lastX) / dt;
            this.velocityY = (point.clientY - this.lastY) / dt;
        }
        this.lastX = point.clientX;
        this.lastY = point.clientY;
        this.lastTime = now;

        // Calculate rotation
        const rotation = Math.min(
            Math.max(this.currentX * this.options.rotationFactor, -this.options.maxRotation),
            this.options.maxRotation
        );

        // Apply transform
        card.style.transform = `translateX(${this.currentX}px) translateY(${this.currentY}px) rotate(${rotation}deg)`;

        // Update swipe indicators
        this.updateIndicators(card);

        if (e.cancelable) e.preventDefault();
    }

    onDragEnd(e) {
        if (!this.isDragging) return;
        this.isDragging = false;

        const card = this.getActiveCard();
        if (!card) return;

        card.classList.remove('dragging');

        // Determine swipe direction
        const absX = Math.abs(this.currentX);
        const absY = Math.abs(this.currentY);
        const velocityMagnitude = Math.sqrt(this.velocityX ** 2 + this.velocityY ** 2);

        // Check for swipe
        const isHorizontalSwipe = absX > this.options.threshold ||
                                   (velocityMagnitude > this.options.velocityThreshold && absX > absY);
        const isUpSwipe = this.currentY < -this.options.threshold ||
                          (this.velocityY < -this.options.velocityThreshold && absY > absX);

        if (isUpSwipe && this.currentY < 0) {
            // Swipe up - cook tonight
            this.triggerSwipe('up');
        } else if (isHorizontalSwipe) {
            if (this.currentX > 0) {
                // Swipe right - like
                this.triggerSwipe('right');
            } else {
                // Swipe left - dislike
                this.triggerSwipe('left');
            }
        } else {
            // Snap back
            this.resetCard(card);
        }
    }

    updateIndicators(card) {
        const nopeLabel = card.querySelector('.swipe-label.nope');
        const yumLabel = card.querySelector('.swipe-label.yum');
        const cookLabel = card.querySelector('.swipe-label.cook');

        const threshold = this.options.threshold;

        if (nopeLabel) {
            const opacity = Math.max(0, Math.min(1, -this.currentX / threshold));
            nopeLabel.style.opacity = opacity;
        }

        if (yumLabel) {
            const opacity = Math.max(0, Math.min(1, this.currentX / threshold));
            yumLabel.style.opacity = opacity;
        }

        if (cookLabel) {
            const opacity = Math.max(0, Math.min(1, -this.currentY / threshold));
            cookLabel.style.opacity = opacity;
        }
    }

    resetIndicators(card) {
        const labels = card.querySelectorAll('.swipe-label');
        labels.forEach(label => label.style.opacity = 0);
    }

    resetCard(card) {
        card.style.transition = 'transform 0.3s ease';
        card.style.transform = '';
        this.resetIndicators(card);

        setTimeout(() => {
            card.style.transition = '';
        }, 300);
    }

    triggerSwipe(direction) {
        const card = this.getActiveCard();
        if (!card) return;

        // Add exit animation class
        card.classList.add(`exit-${direction}`);
        card.style.transform = '';

        // Get recipe data from card
        const recipeData = {
            recipe_id: card.dataset.recipeId,
            name: card.dataset.recipeName,
            image_url: card.dataset.recipeImage,
            category: card.dataset.recipeCategory,
            cuisine: card.dataset.recipeCuisine
        };

        // Trigger callback
        setTimeout(() => {
            this.currentIndex++;
            this.updateCardPositions();

            // Call the appropriate callback
            if (direction === 'left' && this.options.onSwipeLeft) {
                this.options.onSwipeLeft(recipeData);
            } else if (direction === 'right' && this.options.onSwipeRight) {
                this.options.onSwipeRight(recipeData);
            } else if (direction === 'up' && this.options.onSwipeUp) {
                this.options.onSwipeUp(recipeData);
            }

            // Check if we need more cards
            if (this.currentIndex >= this.cards.length - 2) {
                if (this.options.onNeedMoreCards) {
                    this.options.onNeedMoreCards();
                }
            }

            // Check if deck is empty
            if (this.currentIndex >= this.cards.length) {
                if (this.options.onDeckEmpty) {
                    this.options.onDeckEmpty();
                }
            }
        }, 300);
    }

    // Programmatic swipe (for button clicks)
    swipeLeft() {
        if (this.currentIndex < this.cards.length) {
            const card = this.getActiveCard();
            if (card) {
                card.style.transition = 'transform 0.3s ease';
                card.style.transform = 'translateX(-150%) rotate(-30deg)';
                const nopeLabel = card.querySelector('.swipe-label.nope');
                if (nopeLabel) nopeLabel.style.opacity = 1;
            }
            setTimeout(() => this.triggerSwipe('left'), 100);
        }
    }

    swipeRight() {
        if (this.currentIndex < this.cards.length) {
            const card = this.getActiveCard();
            if (card) {
                card.style.transition = 'transform 0.3s ease';
                card.style.transform = 'translateX(150%) rotate(30deg)';
                const yumLabel = card.querySelector('.swipe-label.yum');
                if (yumLabel) yumLabel.style.opacity = 1;
            }
            setTimeout(() => this.triggerSwipe('right'), 100);
        }
    }

    swipeUp() {
        if (this.currentIndex < this.cards.length) {
            const card = this.getActiveCard();
            if (card) {
                card.style.transition = 'transform 0.3s ease';
                card.style.transform = 'translateY(-150%) scale(0.8)';
                const cookLabel = card.querySelector('.swipe-label.cook');
                if (cookLabel) cookLabel.style.opacity = 1;
            }
            setTimeout(() => this.triggerSwipe('up'), 100);
        }
    }

    // Add new cards to the deck
    addCards(cardsHTML) {
        this.cardStack.insertAdjacentHTML('beforeend', cardsHTML);
        this.updateCards();
    }

    // Get remaining card count
    getRemainingCount() {
        return this.cards.length - this.currentIndex;
    }

    // Reset deck
    reset() {
        this.currentIndex = 0;
        this.cards.forEach(card => {
            card.classList.remove('exit-left', 'exit-right', 'exit-up');
            card.style.transform = '';
            this.resetIndicators(card);
        });
        this.updateCardPositions();
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TinderSwipe;
}
