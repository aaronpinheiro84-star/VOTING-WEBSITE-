from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ===============================
# VOTER MODEL
# ===============================
class Voter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    fullname = models.CharField(max_length=100)
    dob = models.DateField()

    gender = models.CharField(
        max_length=10,
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
        ]
    )

    aadhaar_number = models.CharField(max_length=12, unique=True)

    2
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)

    image = models.ImageField(upload_to="profileimage/", null=True, blank=True)

    # Features
    is_approved = models.BooleanField(default=False)
    has_voted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def clean(self):
        if not self.aadhaar_number.isdigit() or len(self.aadhaar_number) != 12:
            raise ValidationError("Aadhaar number must be 12 digits.")

    def __str__(self):
        return f"{self.fullname} ({self.aadhaar_number})"

    class Meta:
        ordering = ['-created_at']


# ===============================
# ELECTION MODEL
# ===============================
class Election(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def clean(self):
        # 🔥 Only one active election allowed
        if self.is_active:
            active = Election.objects.filter(is_active=True).exclude(id=self.id)
            if active.exists():
                raise ValidationError("Another election is already active.")

        # 🔥 Date validation
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_running(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-start_date']


# ===============================
# CANDIDATE MODEL
# ===============================
class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="candidates"
    )

    def __str__(self):
        return f"{self.name} - {self.party}"

    class Meta:
        ordering = ['name']


# ===============================
# VOTE MODEL
# ===============================
class Vote(models.Model):
    voter = models.ForeignKey(
        Voter,   # ✅ VERY IMPORTANT (Not User)
        on_delete=models.CASCADE,
        related_name="votes"
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'election')
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.voter.fullname} → {self.candidate.name}"


from django.db import models

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    photo = models.ImageField(upload_to='voter_photos/', null=True, blank=True)

    voted_at = models.DateTimeField(auto_now_add=True)