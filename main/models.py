from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from decimal import Decimal

class User(models.Model):
    nama = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def setName(self, nama):
        self.nama = nama
        self.save()

    def getName(self):
        return self.nama

    def __str__(self):
        return self.nama

class Kategori(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    nama = models.CharField(max_length=100)
    ikon = models.CharField(max_length=50, blank=True, null=True)
    warna = models.CharField(max_length=7, blank=True, null=True)  # Hex color code

    def getNama(self):
        return self.nama

    def getIkon(self):
        return self.ikon

    def getWarna(self):
        return self.warna

    def setNama(self, nama):
        self.nama = nama
        self.save()

    def setIkon(self, ikon):
        self.ikon = ikon
        self.save()

    def setWarna(self, warna):
        self.warna = warna
        self.save()

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name_plural = "Kategori"

class TipeTransaksi(models.TextChoices):
    PEMASUKAN = 'PEMASUKAN', 'Pemasukan'
    PENGELUARAN = 'PENGELUARAN', 'Pengeluaran'

# Base Transaksi class (Interface implementation)
class Transaksi(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    jumlah = models.DecimalField(max_digits=15, decimal_places=2)
    tanggal = models.DateField()
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True)
    catatan = models.TextField(blank=True, null=True)
    tipe = models.CharField(max_length=20, choices=TipeTransaksi.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def getJumlah(self):
        return self.jumlah

    def getTanggal(self):
        return self.tanggal

    def getTipe(self):
        return self.tipe

    def getKategori(self):
        return self.kategori

    def getCatatan(self):
        return self.catatan

    def setJumlah(self, jumlah):
        self.jumlah = jumlah
        self.save()

    def setTanggal(self, tanggal):
        self.tanggal = tanggal
        self.save()

    def setTipe(self, tipe):
        self.tipe = tipe
        self.save()

    def setKategori(self, kategori):
        self.kategori = kategori
        self.save()

    def setCatatan(self, catatan):
        self.catatan = catatan
        self.save()

    def __str__(self):
        return f"{self.get_tipe_display()} - {self.jumlah} - {self.tanggal}"

    class Meta:
        verbose_name_plural = "Transaksi"

class TransaksiPemasukan(Transaksi):
    sumber_pemasukan = models.CharField(max_length=100, blank=True, null=True)

    def getSumberPemasukan(self):
        return self.sumber_pemasukan

    def setSumberPemasukan(self, sumber):
        self.sumber_pemasukan = sumber
        self.save()

    def save(self, *args, **kwargs):
        self.tipe = TipeTransaksi.PEMASUKAN
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Transaksi Pemasukan"

class TransaksiPengeluaran(Transaksi):
    metode_pembayaran = models.CharField(max_length=100, blank=True, null=True)

    def getMetodePembayaran(self):
        return self.metode_pembayaran

    def setMetodePembayaran(self, metode):
        self.metode_pembayaran = metode
        self.save()

    def save(self, *args, **kwargs):
        self.tipe = TipeTransaksi.PENGELUARAN
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Transaksi Pengeluaran"

# Manager/Service Classes as described in the class diagram
class PengelolaKategori:
    """Service class for managing Kategori operations"""
    
    @staticmethod
    def tambahKategori(kategori):
        """Add a new kategori"""
        kategori.save()
        return kategori

    @staticmethod
    def hapusKategori(id):
        """Delete kategori by id"""
        try:
            kategori = Kategori.objects.get(id=id)
            kategori.delete()
            return True
        except Kategori.DoesNotExist:
            return False

    @staticmethod
    def perbaruiKategori(kategori):
        """Update existing kategori"""
        kategori.save()
        return kategori

    @staticmethod
    def ambilSemuaKategori():
        """Get all kategori"""
        return list(Kategori.objects.all())

class PengelolaTransaksi:
    """Service class for managing Transaksi operations"""
    
    @staticmethod
    def tambahTransaksi(transaksi):
        """Add a new transaksi"""
        transaksi.save()
        return transaksi

    @staticmethod
    def hapusTransaksi(id):
        """Delete transaksi by id"""
        try:
            transaksi = Transaksi.objects.get(id=id)
            transaksi.delete()
            return True
        except Transaksi.DoesNotExist:
            return False

    @staticmethod
    def perbaruiTransaksi(transaksi):
        """Update existing transaksi"""
        transaksi.save()
        return transaksi

    @staticmethod
    def ambilTransaksiBerdasarkanTanggal(tanggal):
        """Get transactions by date"""
        return list(Transaksi.objects.filter(tanggal=tanggal))

    @staticmethod
    def ambilTransaksiBerdasarkanKategori(kategori):
        """Get transactions by category"""
        return list(Transaksi.objects.filter(kategori=kategori))

    @staticmethod
    def hitungTotalBerdasarkanTipe(tipe):
        """Calculate total amount by transaction type"""
        result = Transaksi.objects.filter(tipe=tipe).aggregate(total=Sum('jumlah'))
        return result['total'] or Decimal('0.00')

class LayananRingkasan:
    """Service class for summary calculations"""
    
    @staticmethod
    def hitungTotalBerdasarkanTanggal(tanggal):
        """Calculate total amount by date"""
        result = Transaksi.objects.filter(tanggal=tanggal).aggregate(total=Sum('jumlah'))
        return result['total'] or Decimal('0.00')

    @staticmethod
    def hitungTotalBerdasarkanBulan(bulan, tahun):
        """Calculate total amount by month and year"""
        result = Transaksi.objects.filter(
            tanggal__month=bulan, 
            tanggal__year=tahun
        ).aggregate(total=Sum('jumlah'))
        return result['total'] or Decimal('0.00')

    @staticmethod
    def hitungTotalBerdasarkanKategori(kategori):
        """Calculate total amount by category"""
        result = Transaksi.objects.filter(kategori=kategori).aggregate(total=Sum('jumlah'))
        return result['total'] or Decimal('0.00')