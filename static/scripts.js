document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('pdf-form');
    const fileInput = document.getElementById('file');
    const fileText = document.querySelector('.file-text');
    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results-container');

    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileText.textContent = `Selected: ${fileInput.files[0].name}`;
            step1.classList.remove('active');
            step2.classList.add('active');
            step3.classList.add('active');
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        if (!formData.has('file') || !formData.get('file').size) {
            alert("Please select a PDF file first");
            return;
        }

        submitBtn.disabled = true;
        loading.classList.remove('hidden');
        resultsContainer.classList.add('hidden');

        try {
            const response = await fetch('/parse/', { method: 'POST', body: formData });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Something went wrong');
            }

            displayResults(data);
        } catch (error) {
            resultsContainer.innerHTML = `<div class="error-message">${error.message}</div>`;
        } finally {
            submitBtn.disabled = false;
            loading.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

function displayResults(data) {
    const container = document.getElementById('results-container');
    container.innerHTML = '<h2>Your Extracted Content</h2>'; // Clear previous results

    if (data.text) {
        container.innerHTML += createSection('📝 Text', `<pre>${escapeHtml(data.text)}</pre>`, true);
    }
    if (data.tables && data.tables.length > 0) {
        container.innerHTML += createSection('📊 Tables', createTables(data.tables));
    }
    if (data.images && data.images.length > 0) {
        container.innerHTML += createSection('🖼️ Images', createImages(data.images));
    }
}

function createSection(title, content, canCopy = false) {
    return `
        <div class="result-section">
            <h3>${title} ${canCopy ? '<button class="copy-btn" onclick="copyText(this)">Copy</button>' : ''}</h3>
            ${content}
        </div>
    `;
}

function createTables(tables) {
    return tables.map((tableData, i) => {
        if (!tableData.data || tableData.data.length === 0) return '';
        const headers = Object.keys(tableData.data[0]);
        return `
            <h4>Table ${i + 1} (Page ${tableData.page})</h4>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${tableData.data.map(row => `<tr>${headers.map(h => `<td>${escapeHtml(row[h])}</td>`).join('')}</tr>`).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }).join('');
}

function createImages(images) {
    return `<div class="image-grid">${images.map(img => `
        <div class="image-container">
            <img src="data:image/png;base64,${img.image_base64}" alt="Page ${img.page}, Image ${img.image_number}">
        </div>
    `).join('')}</div>`;
}

function copyText(button) {
    const pre = button.closest('.result-section').querySelector('pre');
    navigator.clipboard.writeText(pre.textContent).then(() => {
        button.textContent = "Copied!";
        setTimeout(() => { button.textContent = "Copy"; }, 2000);
    });
}

function escapeHtml(str) {
    return str.replace(/[&<>"'/]/g, (s) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '/': '&#x2F;'
    }[s]));
}

