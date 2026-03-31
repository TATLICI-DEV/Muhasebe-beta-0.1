document.addEventListener('DOMContentLoaded', () => {
    const uploadInput = document.getElementById('pdf-upload');
    const dropZone = document.getElementById('drop-zone');
    const uploadSection = document.getElementById('upload-section');
    const reviewSection = document.getElementById('review-section');
    const successSection = document.getElementById('success-section');
    const uploadProgress = document.getElementById('upload-progress');
    
    let invoiceQueue = [];
    let currentInvoiceIndex = 0;
    let savedInvoiceIds = [];
    
    // Basit görünüm başlangıcı
    reviewSection.style.display = 'none';
    successSection.style.display = 'none';

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleUpload(e.dataTransfer.files);
        }
    });
    
    uploadInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleUpload(e.target.files);
        }
    });

    async function handleUpload(files) {
        if (!files || files.length === 0) return;
        
        const formData = new FormData();
        let validFilesCount = 0;
        
        for (let i = 0; i < files.length; i++) {
            if (files[i].type === 'application/pdf') {
                formData.append('files', files[i]);
                validFilesCount++;
            }
        }

        if (validFilesCount === 0) {
            alert('Lütfen geçerli PDF dosyaları yükleyin.');
            return;
        }

        // UI changes
        const btn = dropZone.querySelector('.btn-primary');
        const p = dropZone.querySelector('p');
        btn.classList.add('hidden');
        p.classList.add('hidden');
        uploadProgress.classList.remove('hidden');

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            if (result.status === 'success' && result.data.length > 0) {
                invoiceQueue = result.data;
                currentInvoiceIndex = 0;
                savedInvoiceIds = [];
                showCurrentInvoice();
            } else {
                 alert('Yükleme başarısız veya veri bulunamadı.');
                 showSection(uploadSection);
            }
        } catch (error) {
            alert('Yükleme sırasında bir hata oluştu: ' + error.message);
            console.error(error);
            showSection(uploadSection);
        } finally {
            btn.classList.remove('hidden');
            p.classList.remove('hidden');
            uploadProgress.classList.add('hidden');
            uploadInput.value = ''; // reset so same file can be uploaded again
        }
    }
    
    function showCurrentInvoice() {
        const data = invoiceQueue[currentInvoiceIndex];
        populateForm(data);
        
        const reviewTitle = document.getElementById('review-title');
        const btnSave = document.getElementById('btn-save');
        
        const remaining = invoiceQueue.length - currentInvoiceIndex - 1;
        if (invoiceQueue.length > 1) {
            reviewTitle.textContent = `${currentInvoiceIndex + 1}. Fatura İnceleniyor (Kalan: ${remaining})`;
            btnSave.textContent = remaining > 0 ? 'Kaydet ve Sonrakine Geç' : 'Kaydet ve Bitir';
        } else {
            reviewTitle.textContent = 'Fatura Verisi Doğrulama';
            btnSave.textContent = 'Kaydet ve Muhasebeleştir';
        }
        
        showSection(reviewSection);
    }

    function populateForm(data) {
        document.getElementById('invoice_date').value = (data.invoice_date && data.invoice_date.value) || '';
        document.getElementById('invoice_number').value = (data.invoice_number && data.invoice_number.value) || '';
        document.getElementById('vkn').value = (data.vkn && data.vkn.value) || '';
        document.getElementById('company_name').value = (data.company_name && data.company_name.value) || '';
        document.getElementById('base_amount').value = (data.base_amount && data.base_amount.value) || 0;
        document.getElementById('vat_rate').value = (data.vat_rate && data.vat_rate.value) || 0;
        document.getElementById('vat_amount').value = (data.vat_amount && data.vat_amount.value) || 0;
        document.getElementById('total_amount').value = (data.total_amount && data.total_amount.value) || 0;
        document.getElementById('expense_account').value = (data.expense_account && data.expense_account.value) || '770';
        document.getElementById('vat_account').value = (data.vat_account && data.vat_account.value) || '191';
        document.getElementById('vendor_account').value = (data.vendor_account && data.vendor_account.value) || '320';
    }

    // Auto calculate
    document.getElementById('base_amount').addEventListener('input', calculateTotal);
    document.getElementById('vat_rate').addEventListener('input', calculateTotal);
    document.getElementById('vat_amount').addEventListener('input', (e) => {
        const base = parseFloat(document.getElementById('base_amount').value) || 0;
        const vatA = parseFloat(e.target.value) || 0;
        document.getElementById('total_amount').value = (base + vatA).toFixed(2);
    });

    function calculateTotal() {
        const base = parseFloat(document.getElementById('base_amount').value) || 0;
        const rate = parseFloat(document.getElementById('vat_rate').value) || 0;
        const vatAmount = base * (rate / 100);
        document.getElementById('vat_amount').value = vatAmount.toFixed(2);
        document.getElementById('total_amount').value = (base + vatAmount).toFixed(2);
    }

    // Save
    document.getElementById('btn-save').addEventListener('click', async () => {
        const data = {
            invoice_date: document.getElementById('invoice_date').value,
            invoice_number: document.getElementById('invoice_number').value,
            vkn: document.getElementById('vkn').value,
            company_name: document.getElementById('company_name').value,
            base_amount: document.getElementById('base_amount').value,
            vat_rate: document.getElementById('vat_rate').value,
            vat_amount: document.getElementById('vat_amount').value,
            total_amount: document.getElementById('total_amount').value,
            expense_account: document.getElementById('expense_account').value,
            vat_account: document.getElementById('vat_account').value,
            vendor_account: document.getElementById('vendor_account').value
        };

        const btn = document.getElementById('btn-save');
        const originalText = btn.textContent;
        btn.textContent = 'Kaydediliyor...';
        btn.disabled = true;

        try {
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (result.status === 'success') {
                savedInvoiceIds.push(result.invoice_id);
                
                if (currentInvoiceIndex < invoiceQueue.length - 1) {
                    currentInvoiceIndex++;
                    showCurrentInvoice();
                    btn.disabled = false;
                } else {
                    await generateBatchReport();
                }
            } else {
                alert('Kaydetme başarısız oldu.');
                btn.disabled = false;
                const remaining = invoiceQueue.length - currentInvoiceIndex - 1;
                btn.textContent = remaining > 0 ? 'Kaydet ve Sonrakine Geç' : 'Kaydet ve Bitir';
            }
        } catch (error) {
            alert('Kaydetme hatası: ' + error.message);
            btn.disabled = false;
            const remaining = invoiceQueue.length - currentInvoiceIndex - 1;
            btn.textContent = remaining > 0 ? 'Kaydet ve Sonrakine Geç' : 'Kaydet ve Bitir';
        }
    });
    
    async function generateBatchReport() {
        const btn = document.getElementById('btn-save');
        btn.textContent = 'Fişler Birleştiriliyor...';
        btn.disabled = true;

        try {
            const response = await fetch('/api/generate_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invoice_ids: savedInvoiceIds })
            });
            const result = await response.json();
            
            if (result.status === 'success') {
                const container = document.getElementById('download-links-container');
                container.innerHTML = `
                    <a href="${result.pdf_url}" target="_blank" class="btn-primary" style="display:block; margin-bottom:15px; text-decoration: none; text-align: center; font-size: 1.1rem; padding: 15px;">📄 Toplu Yevmiye Fişi (PDF) İndir</a>
                    <a href="${result.excel_url}" target="_blank" class="btn-success" style="display:block; margin-bottom:15px; text-decoration: none; text-align: center; font-size: 1.1rem; padding: 15px;">📊 Toplu Yevmiye Fişi (EXCEL) İndir</a>
                `;
                showSection(successSection);
            } else {
                alert('Toplu rapor oluşturma başarısız: ' + result.message);
                showSection(uploadSection);
            }
        } catch (error) {
            alert('Rapor hatası: ' + error.message);
            showSection(uploadSection);
        } finally {
            btn.textContent = 'Kaydet ve Muhasebeleştir';
            btn.disabled = false;
        }
    }

    document.getElementById('btn-cancel').addEventListener('click', () => {
        showSection(uploadSection);
    });

    document.getElementById('btn-new').addEventListener('click', () => {
        showSection(uploadSection);
    });

    function showSection(sectionToShow) {
        document.querySelectorAll('.section').forEach(sec => {
            sec.classList.remove('active');
            sec.style.display = 'none';
        });
        
        sectionToShow.style.display = 'block';
        setTimeout(() => sectionToShow.classList.add('active'), 10);
    }
    
    // TAB LOGIC
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const targetId = e.target.getAttribute('data-target');
            
            document.getElementById('upload-flow').style.display = 'none';
            document.getElementById('dashboard-section').style.display = 'none';
            document.getElementById('settings-section').style.display = 'none';

            if (targetId === 'upload-flow') {
                document.getElementById('upload-flow').style.display = 'block';
                showSection(uploadSection);
            } else if (targetId === 'dashboard-section') {
                document.getElementById('dashboard-section').style.display = 'block';
                await loadDashboard();
            } else if (targetId === 'settings-section') {
                document.getElementById('settings-section').style.display = 'block';
                await loadSettings();
            }
        });
    });

    async function loadDashboard() {
        try {
            const response = await fetch('/api/invoices');
            const result = await response.json();
            
            if (result.status === 'success') {
                const tbody = document.getElementById('history-tbody');
                tbody.innerHTML = '';
                
                let totalBase = 0;
                let totalVat = 0;
                
                result.data.forEach(inv => {
                    const row = document.createElement('tr');
                    totalBase += (inv.base_amount || 0);
                    totalVat += (inv.vat_amount || 0);
                    const total = (inv.total_amount || 0);
                    
                    row.innerHTML = `
                        <td style="padding: 12px;"><input type="checkbox" class="row-checkbox" value="${inv.id}"></td>
                        <td style="padding: 12px;">${inv.invoice_date || '-'}</td>
                        <td style="padding: 12px;">${inv.invoice_number || '-'}</td>
                        <td style="padding: 12px;">${inv.company_name || '-'}</td>
                        <td style="padding: 12px; font-weight:bold;">${total.toFixed(2)} TL</td>
                    `;
                    tbody.appendChild(row);
                });
                
                document.getElementById('kpi-count').textContent = result.data.length;
                document.getElementById('kpi-base').textContent = totalBase.toFixed(2) + ' TL';
                document.getElementById('kpi-vat').textContent = totalVat.toFixed(2) + ' TL';
                
                // checkbox bindings
                const checkboxes = document.querySelectorAll('.row-checkbox');
                const btnRegen = document.getElementById('btn-re-generate');
                const btnDel = document.getElementById('btn-delete');
                
                const selectAll = document.getElementById('selectAllCheckbox');
                selectAll.checked = false; // reset
                btnRegen.disabled = true;
                btnDel.disabled = true;

                selectAll.addEventListener('change', (e) => {
                    checkboxes.forEach(cb => cb.checked = e.target.checked);
                    btnRegen.disabled = !e.target.checked && checkboxes.length > 0;
                    btnDel.disabled = !e.target.checked && checkboxes.length > 0;
                });
                
                checkboxes.forEach(cb => {
                    cb.addEventListener('change', () => {
                        const anyChecked = Array.from(checkboxes).some(c => c.checked);
                        btnRegen.disabled = !anyChecked;
                        btnDel.disabled = !anyChecked;
                    });
                });
            }
        } catch (error) {
            console.error("Dashboard error:", error);
        }
    }
    
    document.getElementById('btn-re-generate').addEventListener('click', async () => {
        const selected = Array.from(document.querySelectorAll('.row-checkbox:checked')).map(cb => parseInt(cb.value));
        if (selected.length === 0) return;
        
        const btn = document.getElementById('btn-re-generate');
        const origText = btn.textContent;
        btn.textContent = 'Rapor Paketleniyor...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/generate_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invoice_ids: selected })
            });
            const result = await response.json();
            
            if (result.status === 'success') {
                const container = document.getElementById('dashboard-links-container');
                container.innerHTML = `
                    <div style="margin-bottom:10px;"><a href="${result.pdf_url}" target="_blank" class="btn-success">📄 Geçmiş Fişlerden Yevmiye (PDF) İndir</a></div>
                    <div><a href="${result.excel_url}" target="_blank" class="btn-primary">📊 Geçmiş Fişlerden Yevmiye (EXCEL) İndir</a></div>
                `;
            } else {
                alert('Üretim hatası: ' + result.message);
            }
        } catch (error) {
            alert('Hata oluştu');
        } finally {
            btn.textContent = origText;
            btn.disabled = false;
        }
    });

    document.getElementById('btn-delete').addEventListener('click', async () => {
        const selected = Array.from(document.querySelectorAll('.row-checkbox:checked')).map(cb => parseInt(cb.value));
        if (selected.length === 0) return;
        
        if (!confirm(`${selected.length} adet evrak kalıcı olarak silinecek. Emin misiniz?`)) return;

        const btn = document.getElementById('btn-delete');
        const origText = btn.textContent;
        btn.textContent = 'Siliniyor...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/invoices', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invoice_ids: selected })
            });
            const result = await response.json();
            
            if (result.status === 'success') {
                alert(result.message);
                await loadDashboard();
            } else {
                alert('Silme hatası: ' + result.message);
            }
        } catch (error) {
            alert('Hata oluştu');
        } finally {
            btn.textContent = origText;
            btn.disabled = false;
        }
    });

    // SETTINGS LOGIC
    let currentSettings = [];

    async function loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const result = await response.json();
            if (result.status === 'success') {
                currentSettings = result.data;
                renderSettingsTable();
            }
        } catch (error) {
            console.error("Settings error:", error);
        }
    }

    function renderSettingsTable() {
        const tbody = document.getElementById('settings-tbody');
        tbody.innerHTML = '';
        currentSettings.forEach((rule, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="padding: 12px;">${rule.keywords}</td>
                <td style="padding: 12px; font-weight:bold;">${rule.code}</td>
                <td style="padding: 12px; text-align:right;">
                    <button class="btn-primary btn-delete-rule" style="background:#dc2626; border-color:#dc2626; padding: 5px 10px; font-size: 0.8rem;" data-index="${index}">Sil</button>
                </td>
            `;
            tbody.appendChild(row);
        });

        document.querySelectorAll('.btn-delete-rule').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = e.target.getAttribute('data-index');
                currentSettings.splice(idx, 1);
                renderSettingsTable();
            });
        });
    }

    document.getElementById('btn-add-rule').addEventListener('click', () => {
        const kw = document.getElementById('new-keyword').value.trim();
        const cd = document.getElementById('new-code').value.trim();
        if(!kw || !cd) {
            alert('Lütfen kelime ve hesap kodu giriniz.');
            return;
        }
        currentSettings.push({ keywords: kw, code: cd });
        document.getElementById('new-keyword').value = '';
        document.getElementById('new-code').value = '';
        renderSettingsTable();
    });

    document.getElementById('btn-save-settings').addEventListener('click', async () => {
        const btn = document.getElementById('btn-save-settings');
        btn.textContent = 'Kaydediliyor...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentSettings)
            });
            const result = await response.json();
            if (result.status === 'success') {
                alert(result.message);
            } else {
                alert('Kaydetme hatası: ' + result.message);
            }
        } catch (error) {
            alert('Hata oluştu');
        } finally {
            btn.textContent = '💾 Tüm Değişiklikleri Kaydet';
            btn.disabled = false;
        }
    });

});
