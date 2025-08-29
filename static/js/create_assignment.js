
    document.addEventListener('DOMContentLoaded', function() {
        const sections = document.querySelectorAll('.form-section');
        const steps = document.querySelectorAll('.nav-step');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        const progressBar = document.querySelector('.progress-bar');
        let currentSection = 0;
        
        // Initialize form
        showSection(currentSection);
        updateProgress();
        
        // Next button click handler
        nextBtn.addEventListener('click', function() {
            if (validateSection(currentSection)) {
                currentSection++;
                showSection(currentSection);
                updateProgress();
            }
        });
        
        // Previous button click handler
        prevBtn.addEventListener('click', function() {
            currentSection--;
            showSection(currentSection);
            updateProgress();
        });
        
        function showSection(index) {
            // Hide all sections
            sections.forEach(section => section.classList.remove('active'));
            steps.forEach(step => step.classList.remove('active'));
            
            // Show current section
            sections[index].classList.add('active');
            steps[index].classList.add('active');
            
            // Update button visibility
            if (index === 0) {
                prevBtn.disabled = true;
            } else {
                prevBtn.disabled = false;
            }
            
            if (index === sections.length - 1) {
                nextBtn.style.display = 'none';
                submitBtn.style.display = 'block';
            } else {
                nextBtn.style.display = 'block';
                submitBtn.style.display = 'none';
            }
        }
        
        function updateProgress() {
            const progress = ((currentSection + 1) / sections.length) * 100;
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            
            // Update progress text
            document.querySelector('.progress-container small').textContent = 
                `Step ${currentSection + 1} of ${sections.length}`;
        }
        
        function validateSection(index) {
            // Simple validation - in a real app you would add more robust validation
            const currentSection = sections[index];
            const inputs = currentSection.querySelectorAll('input, select, textarea');
            let isValid = true;
            
            inputs.forEach(input => {
                if (input.hasAttribute('required') && !input.value) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            return isValid;
        }
        
        // Add floating label functionality
        const inputs = document.querySelectorAll('.floating-input-group input, .floating-input-group select, .floating-input-group textarea');
        
        inputs.forEach(input => {
            // Check if the input has a value on load
            if (input.value) {
                input.parentNode.querySelector('label').classList.add('active');
            }
            
            // Add event listeners
            input.addEventListener('focus', function() {
                this.parentNode.querySelector('label').classList.add('active');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentNode.querySelector('label').classList.remove('active');
                }
            });
        });
    });
