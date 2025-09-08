// Custom JavaScript for Library Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Confirm delete with SweetAlert2
function confirmDelete(id, nama) {
    Swal.fire({
        title: 'Apakah Anda yakin?',
        text: Anda akan menghapus data peminjaman oleh "${nama}",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#95a5a6',
        confirmButtonText: '<i class="fas fa-trash"></i> Ya, hapus!',
        cancelButtonText: '<i class="fas fa-times"></i> Batal',
        reverseButtons: true,
        customClass: {
            confirmButton: 'btn btn-danger',
            cancelButton: 'btn btn-secondary'
        },
        buttonsStyling: false
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading animation
            Swal.fire({
                title: 'Menghapus...',
                text: 'Sedang menghapus data',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            window.location.href = /hapus/${id};
        }
    });
}

// Form validation
function validateForm() {
    const nama = document.getElementById('nama_peminjam');
    const buku = document.getElementById('nama_buku');
    const tglPinjam = document.getElementById('tanggal_peminjaman');
    
    let isValid = true;
    
    // Remove previous error styles
    [nama, buku, tglPinjam].forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    // Check each field
    if (!nama.value.trim()) {
        nama.classList.add('is-invalid');
        isValid = false;
    }
    
    if (!buku.value.trim()) {
        buku.classList.add('is-invalid');
        isValid = false;
    }
    
    if (!tglPinjam.value) {
        tglPinjam.classList.add('is-invalid');
        isValid = false;
    }
    
    if (!isValid) {
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: 'Harap isi semua field yang wajib diisi!',
            customClass: {
                confirmButton: 'btn btn-primary'
            },
            buttonsStyling: false
        });
    }
    
    return isValid;
}

// Date validation
function validateDates() {
    const tglPinjam = new Date(document.getElementById('tanggal_peminjaman').value);
    const tglKembali = document.getElementById('tanggal_pengembalian').value;
    
    if (tglKembali) {
        const tglKembaliDate = new Date(tglKembali);
        if (tglKembaliDate < tglPinjam) {
            Swal.fire({
                icon: 'error',
                title: 'Tanggal Tidak Valid',
                text: 'Tanggal pengembalian tidak boleh sebelum tanggal peminjaman!',
                customClass: {
                    confirmButton: 'btn btn-primary'
                },
                buttonsStyling: false
            });
            return false;
        }
    }
    return true;
}

// Combined validation for form and dates
function validateAll() {
    return validateForm() && validateDates();
}