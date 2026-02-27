/*
智能办公文档处理助手 - 用户体验增强JavaScript
包含键盘导航、动画控制、无障碍访问等功能
*/

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('用户体验增强脚本已加载');
    
    // ==================== 键盘导航增强 ====================
    
    // 为所有可交互元素添加键盘导航类
    function enhanceKeyboardNavigation() {
        const interactiveElements = [
            'a[href]',
            'button',
            'input',
            'textarea',
            'select',
            '[tabindex]'
        ];
        
        interactiveElements.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                // 添加键盘导航类
                element.classList.add('keyboard-nav-item');
                
                // 为按钮添加Enter键支持
                if (element.tagName === 'BUTTON' || element.getAttribute('role') === 'button') {
                    element.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            this.click();
                        }
                    });
                }
            });
        });
    }
    
    // ==================== 动画控制 ====================
    
    // 检查用户是否偏好减少动画
    function checkReducedMotionPreference() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        if (prefersReducedMotion.matches) {
            document.documentElement.classList.add('reduced-motion');
            console.log('检测到用户偏好减少动画，已禁用非必要动画');
        }
        
        // 监听偏好变化
        prefersReducedMotion.addEventListener('change', (e) => {
            if (e.matches) {
                document.documentElement.classList.add('reduced-motion');
            } else {
                document.documentElement.classList.remove('reduced-motion');
            }
        });
    }
    
    // 平滑滚动增强
    function enhanceSmoothScrolling() {
        // 检查是否应该使用平滑滚动
        if (!document.documentElement.classList.contains('reduced-motion')) {
            document.documentElement.style.scrollBehavior = 'smooth';
        }
        
        // 内部链接平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    
                    // 计算固定导航栏的高度
                    const navbarHeight = document.querySelector('nav')?.offsetHeight || 0;
                    
                    // 平滑滚动到目标位置
                    window.scrollTo({
                        top: targetElement.offsetTop - navbarHeight - 20,
                        behavior: 'smooth'
                    });
                    
                    // 为屏幕阅读器添加焦点
                    targetElement.setAttribute('tabindex', '-1');
                    targetElement.focus();
                }
            });
        });
    }
    
    // ==================== 表单增强 ====================
    
    // 表单验证增强
    function enhanceFormValidation() {
        const forms = document.querySelectorAll('form[data-enhanced="true"]');
        
        forms.forEach(form => {
            // 实时验证
            const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    validateField(this);
                });
                
                input.addEventListener('input', function() {
                    // 输入时移除错误状态
                    if (this.checkValidity()) {
                        this.classList.remove('input-invalid');
                        this.classList.add('input-valid');
                    }
                });
            });
            
            // 提交时验证
            form.addEventListener('submit', function(e) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    
                    // 显示所有错误
                    inputs.forEach(input => {
                        validateField(input);
                    });
                    
                    // 聚焦到第一个错误字段
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            });
        });
        
        function validateField(field) {
            const isValid = field.checkValidity();
            const errorContainer = field.parentElement.querySelector('.error-message');
            
            if (isValid) {
                field.classList.remove('input-invalid');
                field.classList.add('input-valid');
                if (errorContainer) errorContainer.textContent = '';
            } else {
                field.classList.remove('input-valid');
                field.classList.add('input-invalid');
                
                if (errorContainer) {
                    // 显示适当的错误消息
                    let errorMessage = '';
                    if (field.validity.valueMissing) {
                        errorMessage = '此字段为必填项';
                    } else if (field.validity.typeMismatch) {
                        errorMessage = '请输入有效的格式';
                    } else if (field.validity.tooShort) {
                        errorMessage = `内容太短，最少需要 ${field.minLength} 个字符`;
                    } else if (field.validity.tooLong) {
                        errorMessage = `内容太长，最多允许 ${field.maxLength} 个字符`;
                    } else {
                        errorMessage = '输入无效';
                    }
                    
                    errorContainer.textContent = errorMessage;
                    errorContainer.setAttribute('role', 'alert');
                }
            }
        }
    }
    
    // ==================== 加载状态管理 ====================
    
    // 显示加载指示器
    function showLoading(containerId, message = '加载中...') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const loadingHtml = `
            <div class="loading-overlay">
                <div class="loading-content">
                    <div class="loading-indicator"></div>
                    <p class="loading-text">${message}</p>
                </div>
            </div>
        `;
        
        // 保存原始内容
        container.dataset.originalContent = container.innerHTML;
        container.innerHTML = loadingHtml;
    }
    
    // 隐藏加载指示器
    function hideLoading(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (container.dataset.originalContent) {
            container.innerHTML = container.dataset.originalContent;
            delete container.dataset.originalContent;
        } else {
            container.innerHTML = '';
        }
    }
    
    // ==================== 无障碍访问增强 ====================
    
    // 为图片添加alt文本检查
    function checkImageAccessibility() {
        const images = document.querySelectorAll('img:not([alt])');
        
        images.forEach(img => {
            // 如果图片是装饰性的，添加空的alt属性
            if (img.getAttribute('role') === 'presentation' || 
                img.classList.contains('decorative')) {
                img.setAttribute('alt', '');
            } else {
                console.warn('发现缺少alt文本的图片:', img.src);
            }
        });
    }
    
    // 跳过导航链接
    function addSkipNavigation() {
        // 检查是否已存在跳过导航链接
        if (document.getElementById('skip-navigation')) return;
        
        const skipLink = document.createElement('a');
        skipLink.id = 'skip-navigation';
        skipLink.href = '#main-content';
        skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:p-4 focus:bg-white';
        skipLink.textContent = '跳转到主要内容';
        
        // 插入到body开头
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // 为主内容区域添加id
        const mainContent = document.querySelector('main');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
    }
    
    // ==================== 性能优化 ====================
    
    // 图片懒加载
    function setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('img[data-src]');
            
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
    
    // 资源懒加载
    function lazyLoadResources() {
        // 懒加载CSS（优先级较低的资源）
        const lazyStylesheets = document.querySelectorAll('link[data-lazy]');
        
        lazyStylesheets.forEach(link => {
            const media = link.getAttribute('media') || 'all';
            
            // 初始设置为不匹配，加载后恢复
            link.setAttribute('media', 'not all');
            link.onload = function() {
                this.setAttribute('media', media);
            };
        });
    }
    
    // ==================== 触摸设备优化 ====================
    
    // 检测触摸设备
    function detectTouchDevice() {
        const isTouchDevice = 'ontouchstart' in window || 
                              navigator.maxTouchPoints > 0 ||
                              window.matchMedia('(hover: none) and (pointer: coarse)').matches;
        
        if (isTouchDevice) {
            document.documentElement.classList.add('touch-device');
            
            // 增加按钮点击区域
            const buttons = document.querySelectorAll('button, .btn');
            buttons.forEach(btn => {
                btn.classList.add('touch-target');
            });
        }
    }
    
    // ==================== 错误处理增强 ====================
    
    // 全局错误处理
    function setupGlobalErrorHandling() {
        window.addEventListener('error', function(e) {
            console.error('全局错误:', e.error);
            
            // 显示用户友好的错误消息
            showUserNotification('系统发生错误，请稍后重试', 'error');
        });
        
        // Promise未捕获的异常
        window.addEventListener('unhandledrejection', function(e) {
            console.error('未处理的Promise异常:', e.reason);
        });
    }
    
    // 显示用户通知
    function showUserNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `user-notification notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.textContent = message;
        
        // 添加样式
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            backgroundColor: type === 'error' ? '#fee2e2' : 
                           type === 'success' ? '#d1fae5' : '#dbeafe',
            color: type === 'error' ? '#991b1b' : 
                   type === 'success' ? '#065f46' : '#1e40af',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '9999',
            maxWidth: '400px',
            animation: 'slideInUp 0.3s ease-out'
        });
        
        document.body.appendChild(notification);
        
        // 自动消失
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
    
    // ==================== 初始化所有增强功能 ====================
    
    // 运行所有增强功能
    function initializeAllEnhancements() {
        // 无障碍访问
        addSkipNavigation();
        checkImageAccessibility();
        
        // 动画和交互
        checkReducedMotionPreference();
        enhanceSmoothScrolling();
        enhanceKeyboardNavigation();
        
        // 表单增强
        enhanceFormValidation();
        
        // 设备检测和优化
        detectTouchDevice();
        
        // 性能优化
        setupLazyLoading();
        lazyLoadResources();
        
        // 错误处理
        setupGlobalErrorHandling();
        
        console.log('所有用户体验增强功能已初始化');
    }
    
    // 启动初始化
    initializeAllEnhancements();
    
    // ==================== 工具函数导出 ====================
    
    // 将实用函数附加到全局对象
    window.UXEnhancements = {
        showLoading,
        hideLoading,
        showUserNotification,
        enhanceFormValidation
    };
});