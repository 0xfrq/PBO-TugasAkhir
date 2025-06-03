from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from decimal import Decimal
from django.core.exceptions import ValidationError

class User(models.Model):
    nama = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    saldo = models.DecimalField(max_digits=25, decimal_places=2, default=Decimal('0.00'))

    def setName(self, nama):
        self.nama = nama
        self.save()

    def getName(self):
        return self.nama
    
    def getSaldo(self):
        return self.saldo
    
    def setSaldo(self, saldo):
        self.saldo = saldo
        self.save()
    
    def tambahSaldo(self, jumlah):
        """Add amount to balance"""
        self.saldo += jumlah
        self.save()
    
    def kurangiSaldo(self, jumlah):
        """Subtract amount from balance"""
        if self.saldo >= jumlah:
            self.saldo -= jumlah
            self.save()
            return True
        return False
    
    def cekSaldoCukup(self, jumlah):
        """Check if balance is sufficient"""
        return self.saldo >= jumlah

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

    def clean(self):
        """Validate transaction before saving"""
        if self.tipe == TipeTransaksi.PENGELUARAN:
            if not self.user.cekSaldoCukup(self.jumlah):
                raise ValidationError(f"Saldo tidak mencukupi. Saldo saat ini: {self.user.getSaldo()}")

    def save(self, *args, **kwargs):
        # Check if this is a new transaction or an update
        is_new = self.pk is None
        old_amount = None
        old_type = None
        
        if not is_new:
            # Get the old values before updating
            old_transaksi = Transaksi.objects.get(pk=self.pk)
            old_amount = old_transaksi.jumlah
            old_type = old_transaksi.tipe
        
        # Validate the transaction
        self.full_clean()
        
        # If updating an existing transaction, reverse the old transaction effect
        if not is_new:
            if old_type == TipeTransaksi.PEMASUKAN:
                self.user.kurangiSaldo(old_amount)
            elif old_type == TipeTransaksi.PENGELUARAN:
                self.user.tambahSaldo(old_amount)
        
        # Apply the new transaction effect
        if self.tipe == TipeTransaksi.PEMASUKAN:
            self.user.tambahSaldo(self.jumlah)
        elif self.tipe == TipeTransaksi.PENGELUARAN:
            if not self.user.kurangiSaldo(self.jumlah):
                raise ValidationError("Saldo tidak mencukupi untuk transaksi pengeluaran")
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to update user balance"""
        # Reverse the transaction effect when deleting
        if self.tipe == TipeTransaksi.PEMASUKAN:
            self.user.kurangiSaldo(self.jumlah)
        elif self.tipe == TipeTransaksi.PENGELUARAN:
            self.user.tambahSaldo(self.jumlah)
        
        super().delete(*args, **kwargs)

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
        """Add a new transaksi with balance validation"""
        try:
            transaksi.save()
            return transaksi
        except ValidationError as e:
            raise e

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
        """Update existing transaksi with balance validation"""
        try:
            transaksi.save()
            return transaksi
        except ValidationError as e:
            raise e

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

class PengelolaSaldo:
    """Service class for managing user balance operations"""
    
    @staticmethod
    def depositSaldo(user, jumlah, catatan="Deposit Saldo"):
        """Deposit money to user balance by creating income transaction"""
        from datetime import date
        
        # Create income transaction for deposit
        transaksi_deposit = TransaksiPemasukan(
            id=f"DEP_{user.id}_{date.today().strftime('%Y%m%d')}_{int(user.saldo * 100)}",
            jumlah=jumlah,
            tanggal=date.today(),
            user=user,
            catatan=catatan,
            sumber_pemasukan="Deposit Saldo"
        )
        
        try:
            transaksi_deposit.save()
            return transaksi_deposit
        except ValidationError as e:
            raise e
    
    @staticmethod
    def cekSaldoUser(user):
        """Check user balance"""
        return user.getSaldo()
    
    @staticmethod
    def transferSaldo(user_pengirim, user_penerima, jumlah, catatan="Transfer Saldo"):
        """Transfer balance between users"""
        from datetime import date
        
        if not user_pengirim.cekSaldoCukup(jumlah):
            raise ValidationError("Saldo pengirim tidak mencukupi")
        
        try:
            # Create expense transaction for sender
            transaksi_keluar = TransaksiPengeluaran(
                id=f"TRF_OUT_{user_pengirim.id}_{date.today().strftime('%Y%m%d')}_{int(jumlah * 100)}",
                jumlah=jumlah,
                tanggal=date.today(),
                user=user_pengirim,
                catatan=f"{catatan} - ke {user_penerima.nama}",
                metode_pembayaran="Transfer"
            )
            transaksi_keluar.save()
            
            # Create income transaction for receiver
            transaksi_masuk = TransaksiPemasukan(
                id=f"TRF_IN_{user_penerima.id}_{date.today().strftime('%Y%m%d')}_{int(jumlah * 100)}",
                jumlah=jumlah,
                tanggal=date.today(),
                user=user_penerima,
                catatan=f"{catatan} - dari {user_pengirim.nama}",
                sumber_pemasukan="Transfer"
            )
            transaksi_masuk.save()
            
            return {"keluar": transaksi_keluar, "masuk": transaksi_masuk}
        except ValidationError as e:
            raise e

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
    
    @staticmethod
    def ringkasanSaldoUser(user):
        """Get user balance summary"""
        total_pemasukan = Transaksi.objects.filter(
            user=user, 
            tipe=TipeTransaksi.PEMASUKAN
        ).aggregate(total=Sum('jumlah'))['total'] or Decimal('0.00')
        
        total_pengeluaran = Transaksi.objects.filter(
            user=user, 
            tipe=TipeTransaksi.PENGELUARAN
        ).aggregate(total=Sum('jumlah'))['total'] or Decimal('0.00')
        
        return {
            'saldo_saat_ini': user.getSaldo(),
            'total_pemasukan': total_pemasukan,
            'total_pengeluaran': total_pengeluaran,
            'selisih': total_pemasukan - total_pengeluaran
        }