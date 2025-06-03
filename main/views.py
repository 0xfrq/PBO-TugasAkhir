from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from datetime import date, datetime
from .models import (
    User, Kategori, Transaksi, TransaksiPemasukan, TransaksiPengeluaran,
    PengelolaKategori, PengelolaTransaksi, LayananRingkasan, TipeTransaksi
)

def show_main(request):
    """Main dashboard view"""
    context = {
        'title': 'Spending Tracker Dashboard',
        'user_count': User.objects.count(),
        'kategori_count': Kategori.objects.count(),
        'transaksi_count': Transaksi.objects.count(),
    }
    
    # Calculate today's summary if there are transactions
    if Transaksi.objects.exists():
        today = date.today()
        today_total = LayananRingkasan.hitungTotalBerdasarkanTanggal(today)
        context['today_total'] = today_total
    
    return render(request, 'main/dashboard.html', context)

def kategori_list(request):
    """Display all categories"""
    categories = PengelolaKategori.ambilSemuaKategori()
    return render(request, 'main/kategori_list.html', {'categories': categories})

def kategori_create(request):
    """Create new category"""
    if request.method == 'POST':
        id = request.POST.get('id')
        nama = request.POST.get('nama')
        ikon = request.POST.get('ikon', '')
        warna = request.POST.get('warna', '#000000')
        
        # Check if ID already exists
        if Kategori.objects.filter(id=id).exists():
            messages.error(request, 'Category ID already exists!')
            return render(request, 'main/kategori_form.html')
        
        kategori = Kategori(id=id, nama=nama, ikon=ikon, warna=warna)
        PengelolaKategori.tambahKategori(kategori)
        messages.success(request, 'Category created successfully!')
        return redirect('kategori_list')
    
    return render(request, 'main/kategori_form.html')

def kategori_delete(request, kategori_id):
    """Delete category"""
    if PengelolaKategori.hapusKategori(kategori_id):
        messages.success(request, 'Category deleted successfully!')
    else:
        messages.error(request, 'Category not found!')
    return redirect('kategori_list')

def transaksi_list(request):
    """Display all transactions"""
    transactions = Transaksi.objects.all().order_by('-tanggal')
    return render(request, 'main/transaksi_list.html', {'transactions': transactions})

def transaksi_create(request):
    """Create new transaction"""
    if request.method == 'POST':
        # Get form data
        id = request.POST.get('id')
        jumlah = request.POST.get('jumlah')
        tanggal = request.POST.get('tanggal')
        kategori_id = request.POST.get('kategori')
        catatan = request.POST.get('catatan', '')
        tipe = request.POST.get('tipe')
        
        # Get user (for now, get first user or create one)
        user = User.objects.first()
        if not user:
            user = User.objects.create(nama="Default User", email="user@example.com")
        
        # Get category
        kategori = None
        if kategori_id:
            kategori = get_object_or_404(Kategori, id=kategori_id)
        
        # Create transaction based on type
        if tipe == TipeTransaksi.PEMASUKAN:
            sumber = request.POST.get('sumber_pemasukan', '')
            transaksi = TransaksiPemasukan(
                id=id, jumlah=jumlah, tanggal=tanggal,
                kategori=kategori, catatan=catatan, user=user,
                sumber_pemasukan=sumber
            )
        else:
            metode = request.POST.get('metode_pembayaran', '')
            transaksi = TransaksiPengeluaran(
                id=id, jumlah=jumlah, tanggal=tanggal,
                kategori=kategori, catatan=catatan, user=user,
                metode_pembayaran=metode
            )
        
        PengelolaTransaksi.tambahTransaksi(transaksi)
        messages.success(request, 'Transaction created successfully!')
        return redirect('transaksi_list')
    
    # Get categories for form
    categories = PengelolaKategori.ambilSemuaKategori()
    context = {
        'categories': categories,
        'tipe_choices': TipeTransaksi.choices
    }
    return render(request, 'main/transaksi_form.html', context)

def summary_view(request):
    """Display financial summary"""
    context = {}
    
    # Today's summary
    today = date.today()
    context['today_total'] = LayananRingkasan.hitungTotalBerdasarkanTanggal(today)
    
    # This month's summary
    context['month_total'] = LayananRingkasan.hitungTotalBerdasarkanBulan(
        today.month, today.year
    )
    
    # Summary by type
    context['pemasukan_total'] = PengelolaTransaksi.hitungTotalBerdasarkanTipe(
        TipeTransaksi.PEMASUKAN
    )
    context['pengeluaran_total'] = PengelolaTransaksi.hitungTotalBerdasarkanTipe(
        TipeTransaksi.PENGELUARAN
    )
    
    # Net balance
    context['net_balance'] = context['pemasukan_total'] - context['pengeluaran_total']
    
    return render(request, 'main/summary.html', context)

def api_test(request):
    """Test API endpoint for your models"""
    # Test creating some sample data
    try:
        # Create a test user if none exists
        if not User.objects.exists():
            user = User.objects.create(nama="Test User", email="test@example.com")
        
        # Create a test category
        if not Kategori.objects.filter(id="test").exists():
            kategori = Kategori(id="test", nama="Test Category", ikon="🧪", warna="#FF5733")
            PengelolaKategori.tambahKategori(kategori)
        
        # Get counts
        data = {
            'status': 'success',
            'message': 'API working correctly!',
            'users': User.objects.count(),
            'categories': Kategori.objects.count(),
            'transactions': Transaksi.objects.count(),
        }
        
    except Exception as e:
        data = {
            'status': 'error',
            'message': str(e)
        }
    
    return JsonResponse(data)