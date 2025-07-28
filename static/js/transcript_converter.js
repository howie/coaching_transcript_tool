
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadSection = document.getElementById('uploadSection');
    const statusSection = document.getElementById('statusSection');
    const downloadSection = document.getElementById('downloadSection');
    const progressFill = document.getElementById('progressFill');
    const statusMessage = document.getElementById('statusMessage');
    const downloadBtn = document.getElementById('downloadBtn');
    const processAnotherBtn = document.getElementById('processAnotherBtn');

    // File upload handling
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    function handleFileUpload(file) {
        // Validate file type
        const allowedTypes = ['.vtt', '.srt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            alert('Please upload a VTT or SRT file.');
            return;
        }

        // Validate file size (50MB max)
        if (file.size > 50 * 1024 * 1024) {
            alert('File size must be less than 50MB.');
            return;
        }

        // Start processing
        uploadToServer(file);
    }

    function uploadToServer(file) {
        // Show processing section
        uploadSection.style.display = 'none';
        statusSection.style.display = 'block';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Get optional parameters
        const coachName = document.getElementById('coachName').value;
        const clientName = document.getElementById('clientName').value;
        const convertChinese = document.getElementById('convertChinese').checked;
        
        if (coachName) formData.append('coach_name', coachName);
        if (clientName) formData.append('client_name', clientName);
        formData.append('convert_to_traditional_chinese', convertChinese);
        formData.append('output_format', 'excel');

        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 500);

        // Upload file
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Upload failed');
            }
        })
        .then(data => {
            setTimeout(() => {
                statusSection.style.display = 'none';
                downloadSection.style.display = 'block';
                
                // Set up download functionality
                downloadBtn.onclick = function() {
                    // This would typically trigger the actual download
                    // For now, we'll show a success message
                    alert('Download functionality will be implemented with backend integration');
                };
            }, 1000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            alert('Upload failed: ' + error.message);
            resetToUpload();
        });

        // Update status messages
        const messages = [
            'Analyzing file format...',
            'Extracting speaker data...',
            'Processing timestamps...',
            'Generating Excel file...',
            'Almost done...'
        ];
        
        let messageIndex = 0;
        const messageInterval = setInterval(() => {
            if (messageIndex < messages.length) {
                statusMessage.textContent = messages[messageIndex];
                messageIndex++;
            } else {
                clearInterval(messageInterval);
            }
        }, 2000);
    }

    function resetToUpload() {
        uploadSection.style.display = 'block';
        statusSection.style.display = 'none';
        downloadSection.style.display = 'none';
        progressFill.style.width = '0%';
        fileInput.value = '';
    }

    // Process another file button
    if (processAnotherBtn) {
        processAnotherBtn.addEventListener('click', resetToUpload);
    }
});
