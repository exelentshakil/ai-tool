// themes/hello-elements/tool-js/notifications.js
// Notification Management Module

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.maxNotifications = 5;
        this.defaultDuration = 4000;
        this.zIndex = 10000;

        this.createContainer();
        console.log('✅ Notification Manager initialized');
    }

    createContainer() {
        // Remove existing container if it exists
        const existingContainer = document.getElementById('notification-container');
        if (existingContainer) {
            existingContainer.remove();
        }

        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container-enhanced';

        // Add styles directly to avoid CSS dependency issues
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: ${this.zIndex};
            pointer-events: none;
            max-width: 400px;
            width: 100%;
        `;

        document.body.appendChild(this.container);
        this.injectStyles();
    }

    injectStyles() {
        if (document.getElementById('notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification-container-enhanced {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            .notification-enhanced {
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
                border-left: 4px solid #667eea;
                padding: 0;
                min-height: 60px;
                opacity: 0;
                transform: translateX(100%);
                transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                pointer-events: auto;
                overflow: hidden;
                position: relative;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .notification-enhanced.show {
                opacity: 1;
                transform: translateX(0);
            }

            .notification-enhanced.success {
                border-left-color: #48bb78;
                background: linear-gradient(135deg, rgba(72, 187, 120, 0.1), rgba(255, 255, 255, 0.95));
            }

            .notification-enhanced.error {
                border-left-color: #e53e3e;
                background: linear-gradient(135deg, rgba(229, 62, 62, 0.1), rgba(255, 255, 255, 0.95));
            }

            .notification-enhanced.warning {
                border-left-color: #ed8936;
                background: linear-gradient(135deg, rgba(237, 137, 54, 0.1), rgba(255, 255, 255, 0.95));
            }

            .notification-enhanced.info {
                border-left-color: #4299e1;
                background: linear-gradient(135deg, rgba(66, 153, 225, 0.1), rgba(255, 255, 255, 0.95));
            }

            .notification-content {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                gap: 12px;
                position: relative;
                z-index: 2;
            }

            .notification-icon {
                font-size: 1.5rem;
                flex-shrink: 0;
                line-height: 1;
            }

            .notification-message {
                flex: 1;
                font-size: 0.95rem;
                line-height: 1.4;
                color: #2d3748;
                font-weight: 500;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s ease;
                color: #718096;
                flex-shrink: 0;
            }

            .notification-close:hover {
                background: rgba(0, 0, 0, 0.1);
                color: #2d3748;
            }

            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width linear;
                border-radius: 0 0 12px 0;
            }

            .notification-enhanced.success .notification-progress {
                background: linear-gradient(90deg, #48bb78, #38a169);
            }

            .notification-enhanced.error .notification-progress {
                background: linear-gradient(90deg, #e53e3e, #c53030);
            }

            .notification-enhanced.warning .notification-progress {
                background: linear-gradient(90deg, #ed8936, #dd6b20);
            }

            .notification-enhanced.info .notification-progress {
                background: linear-gradient(90deg, #4299e1, #3182ce);
            }

            /* Floating animation */
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-2px); }
            }

            .notification-enhanced.show {
                animation: float 3s ease-in-out infinite;
            }

            /* Mobile responsive */
            @media (max-width: 480px) {
                .notification-container-enhanced {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                    max-width: none;
                }

                .notification-content {
                    padding: 14px 16px;
                    gap: 10px;
                }

                .notification-icon {
                    font-size: 1.3rem;
                }

                .notification-message {
                    font-size: 0.9rem;
                }
            }

            /* High contrast mode */
            @media (prefers-contrast: high) {
                .notification-enhanced {
                    border-width: 2px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }
            }

            /* Reduced motion */
            @media (prefers-reduced-motion: reduce) {
                .notification-enhanced {
                    transition: opacity 0.2s ease;
                    animation: none;
                }

                .notification-enhanced.show {
                    animation: none;
                }
            }
        `;

        document.head.appendChild(style);
    }

    show(type = 'info', message, options = {}) {
        const config = {
            duration: this.defaultDuration,
            closable: true,
            persistent: false,
            id: null,
            action: null,
            ...options
        };

        // Remove existing notification with same ID if provided
        if (config.id) {
            this.remove(config.id);
        }

        // Limit number of notifications
        while (this.notifications.length >= this.maxNotifications) {
            this.removeOldest();
        }

        const notification = this.createNotification(type, message, config);
        this.notifications.push(notification);
        this.container.appendChild(notification.element);

        // Show animation
        setTimeout(() => {
            notification.element.classList.add('show');
        }, 10);

        // Auto remove if not persistent
        if (!config.persistent && config.duration > 0) {
            notification.timer = setTimeout(() => {
                this.remove(notification.id);
            }, config.duration);

            // Add progress bar
            this.addProgressBar(notification, config.duration);
        }

        // Track analytics
        this.trackNotification(type, message);

        return notification.id;
    }

    createNotification(type, message, config) {
        const id = config.id || 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const element = document.createElement('div');
        element.className = `notification-enhanced ${type}`;
        element.dataset.id = id;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        let actionButton = '';
        if (config.action) {
            actionButton = `
                <button class="notification-action" data-action="${config.action.type}" style="
                    background: ${this.getActionButtonColor(type)};
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    cursor: pointer;
                    margin-left: 8px;
                    font-weight: 600;
                    transition: all 0.2s ease;
                ">
                    ${config.action.label}
                </button>
            `;
        }

        element.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${icons[type] || icons.info}</span>
                <span class="notification-message">${this.sanitizeMessage(message)}</span>
                ${actionButton}
                ${config.closable ? '<button class="notification-close">&times;</button>' : ''}
            </div>
            ${!config.persistent && config.duration > 0 ? '<div class="notification-progress" style="width: 100%;"></div>' : ''}
        `;

        // Event listeners
        if (config.closable) {
            const closeBtn = element.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => {
                this.remove(id);
            });
        }

        // Action button handler
        if (config.action) {
            const actionBtn = element.querySelector('.notification-action');
            actionBtn.addEventListener('click', () => {
                this.handleAction(config.action, id);
            });

            actionBtn.addEventListener('mouseenter', () => {
                actionBtn.style.transform = 'scale(1.05)';
            });

            actionBtn.addEventListener('mouseleave', () => {
                actionBtn.style.transform = 'scale(1)';
            });
        }

        // Click to dismiss (except on buttons)
        element.addEventListener('click', (e) => {
            if (!e.target.closest('button') && config.closable) {
                this.remove(id);
            }
        });

        return {
            id,
            element,
            type,
            message,
            config,
            timer: null,
            createdAt: Date.now()
        };
    }

    getActionButtonColor(type) {
        const colors = {
            success: '#38a169',
            error: '#c53030',
            warning: '#dd6b20',
            info: '#3182ce'
        };
        return colors[type] || colors.info;
    }

    sanitizeMessage(message) {
        const div = document.createElement('div');
        div.textContent = message;
        return div.innerHTML;
    }

    addProgressBar(notification, duration) {
        const progressBar = notification.element.querySelector('.notification-progress');
        if (!progressBar) return;

        progressBar.style.width = '100%';
        progressBar.style.transition = `width ${duration}ms linear`;

        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 10);
    }

    handleAction(action, notificationId) {
        switch (action.type) {
            case 'reload':
                location.reload();
                break;
            case 'retry':
                if (typeof action.callback === 'function') {
                    action.callback();
                }
                break;
            case 'link':
                if (action.url) {
                    window.open(action.url, action.target || '_blank');
                }
                break;
            case 'callback':
                if (typeof action.callback === 'function') {
                    action.callback();
                }
                break;
        }

        // Remove notification after action
        this.remove(notificationId);
    }

    remove(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;

        // Clear timer
        if (notification.timer) {
            clearTimeout(notification.timer);
        }

        // Hide animation
        notification.element.classList.remove('show');

        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.remove();
            }
        }, 300);

        // Remove from array
        this.notifications = this.notifications.filter(n => n.id !== id);
    }

    removeOldest() {
        if (this.notifications.length === 0) return;

        const oldest = this.notifications.reduce((prev, current) => {
            return prev.createdAt < current.createdAt ? prev : current;
        });

        this.remove(oldest.id);
    }

    clear() {
        this.notifications.forEach(notification => {
            this.remove(notification.id);
        });
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show('success', message, options);
    }

    error(message, options = {}) {
        return this.show('error', message, options);
    }

    warning(message, options = {}) {
        return this.show('warning', message, options);
    }

    info(message, options = {}) {
        return this.show('info', message, options);
    }

    // Persistent notifications
    persistent(type, message, options = {}) {
        return this.show(type, message, { ...options, persistent: true, duration: 0 });
    }

    // Loading notification
    loading(message = 'Loading...', options = {}) {
        return this.show('info', `⏳ ${message}`, {
            ...options,
            persistent: true,
            closable: false
        });
    }

    // Progress notification
    progress(message, percentage, options = {}) {
        const progressMessage = `${message} (${percentage}%)`;
        return this.show('info', progressMessage, options);
    }

    // Get notification count
    getCount() {
        return this.notifications.length;
    }

    // Get all notifications
    getAll() {
        return [...this.notifications];
    }

    // Check if notification exists
    exists(id) {
        return this.notifications.some(n => n.id === id);
    }

    // Update existing notification
    update(id, message, options = {}) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return false;

        const messageElement = notification.element.querySelector('.notification-message');
        if (messageElement) {
            messageElement.innerHTML = this.sanitizeMessage(message);
        }

        // Update type if provided
        if (options.type && options.type !== notification.type) {
            notification.element.className = `notification-enhanced ${options.type} show`;
            notification.type = options.type;
        }

        return true;
    }

    trackNotification(type, message) {
        // Track notification analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'notification_shown', {
                notification_type: type,
                notification_message: message.substring(0, 100) // First 100 chars only
            });
        }

        console.log(`[Notification] ${type.toUpperCase()}: ${message}`);
    }

    // Destroy and cleanup
    destroy() {
        this.clear();
        if (this.container && this.container.parentNode) {
            this.container.remove();
        }

        const styles = document.getElementById('notification-styles');
        if (styles) {
            styles.remove();
        }

        console.log('🧹 Notification Manager destroyed');
    }
}

// Export for global access
window.NotificationManager = NotificationManager;