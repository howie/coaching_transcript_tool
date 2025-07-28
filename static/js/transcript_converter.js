
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const uploadBtn = document.getElementById('uploadBtn');
    const transcriptForm = document.getElementById('transcriptForm');
    const processingStatus = document.getElementById('processingStatus');
    const progressFill = document.getElementById('progressFill');

    // File selection handlers
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    function handleDragOver(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    }

    function handleFileSelect() {
        const file = fileInput.files[0];
        if (file) {
            // Validate file type
            const validTypes = ['.vtt', '.srt'];
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!validTypes.includes(fileExt)) {
                showFlashMessage('Please select a valid VTT or SRT file.', 'error');
                fileInput.value = '';
                uploadBtn.disabled = true;
                return;
            }

            // Validate file size (10MB max)
            if (file.size > 10 * 1024 * 1024) {
                showFlashMessage('File size must be less than 10MB.', 'error');
                fileInput.value = '';
                uploadBtn.disabled = true;
                return;
            }

            // Update UI
            updateUploadArea(file);
            uploadBtn.disabled = false;
        } else {
            resetUploadArea();
            uploadBtn.disabled = true;
        }
    }

    function updateUploadArea(file) {
        uploadArea.innerHTML = `
            <div class="upload-icon">
                <i class="fas fa-file-alt"></i>
            </div>
            <div class="upload-text">${file.name}</div>
            <div class="upload-subtext">File ready for upload</div>
            <div class="upload-info">
                <small>Size: ${formatFileSize(file.size)}</small>
            </div>
        `;
    }

    function resetUploadArea() {
        uploadArea.innerHTML = `
            <div class="upload-icon">
                <i class="fas fa-cloud-upload-alt"></i>
            </div>
            <div class="upload-text">Drop your transcript file here</div>
            <div class="upload-subtext">or click to browse</div>
            <div class="upload-info">
                <small>Supported formats: .vtt, .srt (Max size: 10MB)</small>
            </div>
        `;
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Form submission
    transcriptForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showFlashMessage('Please select a file first.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('coach_name', document.getElementById('coachName').value);
        formData.append('client_name', document.getElementById('clientName').value);
        formData.append('convert_to_traditional_chinese', document.getElementById('convertChinese').checked);

        // Show processing status
        transcriptForm.style.display = 'none';
        processingStatus.style.display = 'block';
        
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);

        try {
            const response = await fetch('/api/convert-transcript', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            progressFill.style.width = '100%';

            if (response.ok) {
                const blob = await response.blob();
                const filename = getFilenameFromResponse(response) || 'transcript.xlsx';
                
                // Download file
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                showFlashMessage('File converted successfully!', 'success');
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Conversion failed');
            }
        } catch (error) {
            clearInterval(progressInterval);
            console.error('Error:', error);
            showFlashMessage(error.message || 'An error occurred during conversion.', 'error');
            
            // Reset form
            setTimeout(() => {
                processingStatus.style.display = 'none';
                transcriptForm.style.display = 'block';
                progressFill.style.width = '0%';
            }, 2000);
        }
    });

    function getFilenameFromResponse(response) {
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename=(.+)/);
            if (filenameMatch) {
                return filenameMatch[1].replace(/"/g, '');
            }
        }
        return null;
    }

    function showFlashMessage(message, type) {
        const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
        
        const flashMessage = document.createElement('div');
        flashMessage.className = `flash-message ${type}`;
        flashMessage.textContent = message;
        
        flashContainer.appendChild(flashMessage);
        
        setTimeout(() => {
            flashMessage.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => flashMessage.remove(), 300);
        }, 5000);
    }

    function createFlashContainer() {
        const container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
        return container;
    }
});
