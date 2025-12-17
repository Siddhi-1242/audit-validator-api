const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileNameDisplay = document.getElementById('fileName');
const validateBtn = document.getElementById('validateBtn');
const resultsSection = document.getElementById('resultsSection');
const statusBanner = document.getElementById('statusBanner');
const overallStatusLabel = document.getElementById('overallStatusLabel');

let currentFile = null;

uploadArea.addEventListener('click', (e) => {
    if (e.target !== validateBtn) fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        currentFile = e.target.files[0];
        fileNameDisplay.textContent = currentFile.name;
        validateBtn.disabled = false;
        resultsSection.classList.add('results-hidden');
    }
});

validateBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    validateBtn.textContent = 'Processing...';
    validateBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/audit/validate-pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        validateBtn.textContent = 'Validate Document';
        validateBtn.disabled = false;
    }
});

function renderResults(data) {
    resultsSection.classList.remove('results-hidden');

    // Overall Status
    const status = data.overall_status;
    overallStatusLabel.textContent = status;
    statusBanner.className = 'status-banner ' + (status === 'PASS' ? 'status-pass' : 'status-fail');

    // PAGE 1: HEADER
    const p1Container = document.getElementById('page1Results');
    p1Container.innerHTML = '';
    const p1Fields = data.page_1.fields;

    // Define Field Maps
    const headerMap = {
        'company_name': 'Company Name',
        'year': 'Year / Period End',
        'completed_by': 'Completed By',
        'date': 'Date'
    };

    // Render Page 1 Cards
    for (const [key, label] of Object.entries(headerMap)) {
        const fieldData = p1Fields[key] || { valid: false, error: "Missing", value: "" };
        const card = createCard(label, fieldData);
        p1Container.appendChild(card);
    }

    // PAGE 2: TABLE
    const p2Container = document.getElementById('page2Results');
    p2Container.innerHTML = '';
    const rows = data.page_2.rows;

    if (!rows || rows.length === 0) {
        p2Container.innerHTML = '<div class="no-data">No table data found on Page 2</div>';
    } else {
        rows.forEach(row => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'row-card';

            const statusBadge = row.row_status === 'PASS'
                ? '<span class="badge-pass">PASS</span>'
                : '<span class="badge-fail">FAIL</span>';

            rowDiv.innerHTML = `
                <div class="row-header">
                    <h4>Row ${row.row_number}</h4>
                    ${statusBadge}
                </div>
                <div class="row-fields">
                    ${createMiniField("Name", row.fields.business_person_name)}
                    ${createMiniField("Criteria", row.fields.criteria_code)}
                    ${createMiniField("Type", row.fields.transaction_type)}
                </div>
            `;
            p2Container.appendChild(rowDiv);
        });
    }
}

function createCard(label, data) {
    const isValid = data.valid;
    const valueStr = data.value || '<span class="empty">Empty</span>';
    const errorHtml = data.error ? `<div class="error-msg">${data.error}</div>` : '';

    const div = document.createElement('div');
    div.className = `result-card ${isValid ? 'card-valid' : 'card-invalid'}`;
    div.innerHTML = `
        <div>
            <div class="field-name">${label}</div>
            <div class="field-value">${valueStr}</div>
            ${errorHtml}
        </div>
        <div class="field-status" style="color: ${isValid ? 'var(--success)' : 'var(--error)'}">
            ${isValid ? 'VALID' : 'INVALID'}
        </div>
    `;
    return div;
}

function createMiniField(label, data) {
    const colorClass = data.valid ? 'text-success' : 'text-error';
    const errText = data.error ? `<div class="mini-error">${data.error}</div>` : '';
    return `
        <div class="mini-field">
            <span class="mini-label">${label}:</span>
            <span class="mini-value ${colorClass}">${data.value || "Empty"}</span>
            ${errText}
        </div>
    `;
}
