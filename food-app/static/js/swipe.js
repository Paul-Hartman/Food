/**
 * Swipe Handler for Cooking Cards
 * Touch gesture support for mobile devices
 */

class SwipeHandler {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            threshold: 80, // Minimum distance for swipe
            restraint: 100, // Maximum perpendicular distance
            allowedTime: 500, // Max time for swipe
            onSwipeLeft: null,
            onSwipeRight: null,
            onSwipeUp: null,
            onSwipeDown: null,
            ...options
        };

        this.startX = 0;
        this.startY = 0;
        this.startTime = 0;
        this.distX = 0;
        this.distY = 0;

        this.init();
    }

    init() {
        this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        this.element.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: true });
        this.element.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }

    handleTouchStart(e) {
        const touch = e.changedTouches[0];
        this.startX = touch.pageX;
        this.startY = touch.pageY;
        this.startTime = new Date().getTime();
        this.distX = 0;
        this.distY = 0;
    }

    handleTouchMove(e) {
        const touch = e.changedTouches[0];
        this.distX = touch.pageX - this.startX;
        this.distY = touch.pageY - this.startY;
    }

    handleTouchEnd(e) {
        const elapsedTime = new Date().getTime() - this.startTime;

        if (elapsedTime <= this.options.allowedTime) {
            // Horizontal swipe
            if (Math.abs(this.distX) >= this.options.threshold &&
                Math.abs(this.distY) <= this.options.restraint) {
                if (this.distX < 0 && this.options.onSwipeLeft) {
                    this.options.onSwipeLeft();
                } else if (this.distX > 0 && this.options.onSwipeRight) {
                    this.options.onSwipeRight();
                }
            }
            // Vertical swipe
            else if (Math.abs(this.distY) >= this.options.threshold &&
                     Math.abs(this.distX) <= this.options.restraint) {
                if (this.distY < 0 && this.options.onSwipeUp) {
                    this.options.onSwipeUp();
                } else if (this.distY > 0 && this.options.onSwipeDown) {
                    this.options.onSwipeDown();
                }
            }
        }
    }
}

// Export for use
window.SwipeHandler = SwipeHandler;
