document.addEventListener('DOMContentLoaded', () => {
    const repoUrl = document.getElementById('repo-url');
    const repoExplorer = document.getElementById('repo-explorer');
    const fileList = document.getElementById('file-list');
    const sourceCode = document.getElementById('source-code');
    const convertedCode = document.getElementById('converted-code');
    const targetLanguage = document.getElementById('target-language');
    const convertBtn = document.getElementById('convert-btn');
    const loading = document.getElementById('loading');
    const sourceLanguageDisplay = document.getElementById('source-language-display');
    const targetLanguageDisplay = document.getElementById('target-language-display');

    let currentRepo = '';
    let currentFile = '';
    let currentLanguage = '';

    repoExplorer.classList.remove('hidden');

    repoUrl.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            await exploreRepository();
        }
    });

    async function exploreRepository() {
        const repoUrlValue = repoUrl.value.trim();
        showLoading('Exploring repository...');
        sourceCode.value = '';
        convertedCode.value = '';

        try {
            const response = await fetch('/repo-convert/explore', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({repo_url: repoUrlValue}),
            });

            const data = await response.json();
            currentRepo = data.repo_url;
            renderFileList(data.files);
        } finally {
            hideLoading();
        }
    }

    function renderFileList(files) {
        if (!files || files.length === 0) {
            fileList.innerHTML = '<p class="text-gray-500">No files found</p>';
            return;
        }

        files.sort((a, b) => a.path.localeCompare(b.path));
        fileList.innerHTML = files.map(file => {
            return `<div class="file-item py-1 px-2 hover:bg-gray-100 cursor-pointer" data-path="${file.path}">${file.path}</div>`;
        }).join('');

        document.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', async () => {
                const filePath = item.getAttribute('data-path');
                await fetchFileContent(filePath);
            });
        });
    }

    async function fetchFileContent(filePath) {
        showLoading('Fetching file...');
        sourceCode.value = '';
        convertedCode.value = '';

        try {
            const response = await fetch('/repo-convert/fetch-file', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    repo_url: currentRepo,
                    file_path: filePath
                }),
            });

            const data = await response.json();
            currentFile = filePath;
            currentLanguage = data.language;
            sourceCode.value = data.content;
            sourceLanguageDisplay.textContent = `Language: ${currentLanguage}`;
            targetLanguageDisplay.textContent = '';

            document.querySelectorAll('.file-item').forEach(item => {
                item.classList.remove('bg-blue-100');
                if (item.getAttribute('data-path') === filePath) {
                    item.classList.add('bg-blue-100');
                }
            });

            convertBtn.classList.remove('hidden');
        } finally {
            hideLoading();
        }
    }

    convertBtn.addEventListener('click', async () => {
        showLoading('Converting code...');
        convertedCode.value = '';

        try {
            const response = await fetch('/repo-convert/convert', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    repo_url: currentRepo,
                    file_path: currentFile,
                    source_language: currentLanguage,
                    target_language: targetLanguage.value
                }),
            });

            const data = await response.json();
            convertedCode.value = data.converted_code;
            targetLanguageDisplay.textContent = `Language: ${targetLanguage.value}`;
        } finally {
            hideLoading();
        }
    });

    function showLoading(message) {
        loading.querySelector('p').textContent = message;
        loading.classList.remove('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }
});