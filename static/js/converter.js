
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const statusSection = document.getElementById('statusSection');
    const downloadSection = document.getElementById('downloadSection');
    const statusTitle = document.getElementById('statusTitle');
    const statusMessage = document.getElementById('statusMessage');
    const progressFill = document.getElementById('progressFill');
    const downloadBtn = document.getElementById('downloadBtn');

    // File upload handling
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    function handleFileUpload(file) {
        // Validate file type
        const validTypes = ['.vtt', '.srt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            alert('Please upload a valid VTT or SRT file.');
            return;
        }

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB.');
            return;
        }

        // Show processing status
        document.querySelector('.upload-section').style.display = 'none';
        statusSection.style.display = 'block';
        
        // Simulate upload progress
        simulateProgress();
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('coach_name', document.getElementById('coachName').value);
        formData.append('client_name', document.getElementById('clientName').value);
        formData.append('convert_to_traditional_chinese', document.getElementById('traditionalChinese').checked);

        // Upload file
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showDownloadReady(data.filename);
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred while processing your file.');
        });
    }

    function simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
            
            if (progress >= 90) {
                clearInterval(interval);
            }
        }, 200);
    }

    function showDownloadReady(filename) {
        statusSection.style.display = 'none';
        downloadSection.style.display = 'block';
        
        // For demo purposes, we'll just show a success message
        // In production, this would handle the actual file download
        downloadBtn.addEventListener('click', () => {
            alert(`Download would start for: ${filename}\n\nThis is a demo. File processing will be integrated with your existing FastAPI backend.`);
        });
    }

    function showError(errorMessage) {
        statusTitle.textContent = 'Processing Failed';
        statusMessage.textContent = errorMessage;
        document.querySelector('.status-icon i').className = 'fas fa-exclamation-triangle';
        document.querySelector('.status-icon').style.color = '#dc3545';
        
        // Show restart button
        setTimeout(() => {
            const restartBtn = document.createElement('button');
            restartBtn.className = 'btn btn-primary';
            restartBtn.innerHTML = '<i class="fas fa-arrow-left"></i> Try Again';
            restartBtn.onclick = () => location.reload();
            statusSection.querySelector('.status-content').appendChild(restartBtn);
        }, 2000);
    }
});
