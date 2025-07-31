
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const uploadBtn = document.getElementById('uploadBtn');
    const transcriptForm = document.getElementById('transcriptForm');
    const processingStatus = document.getElementById('processingStatus');
    const downloadSection = document.getElementById('downloadSection');
    const downloadLink = document.getElementById('downloadLink');
    const progressFill = document.getElementById('progressFill');

    // File selection handler
    fileInput.addEventListener('change', handleFileSelect);

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

    // Form submission using XMLHttpRequest for better compatibility
    transcriptForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput.files[0]) {
            showFlashMessage('Please select a file first.', 'error');
            return;
        }
        
        const selectedFile = fileInput.files[0];

        // Create FormData manually to avoid CSS positioning issues
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('coach_name', document.getElementById('coachName').value);
        formData.append('client_name', document.getElementById('clientName').value);
        if (document.getElementById('convertChinese').checked) {
            formData.append('convert_to_traditional_chinese', 'on');
        }
        
        const xhr = new XMLHttpRequest();

        xhr.open('POST', '/upload', true);

        // Update progress bar
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
            }
        };

        // Handle completion
        xhr.onload = function() {
            progressFill.style.width = '100%';
            if (xhr.status === 200) {
                const blob = xhr.response;
                const contentDisposition = xhr.getResponseHeader('Content-Disposition');
                let filename = 'transcript.xlsx';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                // Create a link to download the file
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Update UI
                processingStatus.style.display = 'none';
                downloadSection.style.display = 'block';
                showFlashMessage('File converted successfully!', 'success');

            } else {
                // Handle error
                let errorMsg = 'An error occurred during conversion.';
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    errorMsg = errorData.error || errorMsg;
                } catch (e) {
                    // Response is not JSON
                }
                handleUploadError(errorMsg);
            }
        };

        // Handle network errors
        xhr.onerror = function() {
            handleUploadError('A network error occurred. Please try again.');
        };

        // Show processing status and send request
        transcriptForm.style.display = 'none';
        processingStatus.style.display = 'block';
        progressFill.style.width = '0%';
        xhr.responseType = 'blob';
        xhr.send(formData);
    });

    function handleUploadError(message) {
        console.error('Error:', message);
        showFlashMessage(message, 'error');
        
        // Reset form
        setTimeout(() => {
            processingStatus.style.display = 'none';
            transcriptForm.style.display = 'block';
            progressFill.style.width = '0%';
            resetUploadArea();
            uploadBtn.disabled = true;
            fileInput.value = '';
        }, 2000);
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
