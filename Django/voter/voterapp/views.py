from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count

from .models import Voter, Candidate, Vote, Election


# ---------------- INDEX ----------------
def index(request):
    return render(request, 'voterapp/index.html')


from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from .models import Voter


def registration(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname").strip()
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        aadhaar_number = request.POST.get("aadhaar_number").strip()
        mobile = request.POST.get("mobile").strip()
        email = request.POST.get("email").strip()
        address = request.POST.get("address").strip()
        password = request.POST.get("password").strip()   # 🔥 IMPORTANT

        if User.objects.filter(username=aadhaar_number).exists():
            messages.error(request, "Aadhaar Number already registered.")
            return redirect("register")

        try:
            user = User.objects.create_user(
                username=aadhaar_number,
                password=password
            )

            Voter.objects.create(
                user=user,
                fullname=fullname,
                dob=dob,
                gender=gender,
                aadhaar_number=aadhaar_number,
                mobile=mobile,
                email=email,
                address=address,
                is_approved=False
            )

            messages.success(request, "Registration successful. Wait for admin approval.")
            return redirect("login")

        except Exception as e:
            print("REGISTRATION ERROR:", e)
            messages.error(request, "Registration failed. Try again.")
            return redirect("register")

    return render(request, "voterapp/register.html")









from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Voter



from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Voter


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username').strip()
        password = request.POST.get('password').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:

            # 🔥 SUPERUSER LOGIN (Admin)
            if user.is_superuser:
                auth_login(request, user)
                return redirect('admin_dashboard')

            # 🔥 NORMAL VOTER LOGIN
            try:
                voter = Voter.objects.get(user=user)

                if not voter.is_approved:
                    messages.error(request, "Your account is not approved yet.")
                    return redirect('login')

                auth_login(request, user)
                return redirect('home')

            except Voter.DoesNotExist:
                messages.error(request, "Voter profile not found.")
                return redirect('login')

        else:
            messages.error(request, "Invalid Username or Password")
            return redirect('login')

    return render(request, 'voterapp/login.html')


# ---------------- HOME ----------------
@login_required
def home(request):
    election = Election.objects.filter(is_active=True).first()

    try:
        voter_profile = Voter.objects.get(user=request.user)
    except Voter.DoesNotExist:
        messages.error(request, "Voter profile not found.")
        return redirect("logout")

    has_voted = False
    is_running = False
    time_remaining_seconds = 0
    candidates = None   # ✅ ADD THIS

    if election:
        is_running = election.is_running()

        has_voted = Vote.objects.filter(
            voter=voter_profile,
            election=election
        ).exists()

        # ✅ ADD THIS
        candidates = Candidate.objects.filter(election=election)

        if is_running:
            remaining = election.end_date - timezone.now()
            time_remaining_seconds = max(int(remaining.total_seconds()), 0)

            print("Approved:", voter_profile.is_approved)
            print("Has voted:", has_voted)
            print("Candidates:", candidates)


    context = {
        "election": election,
        "voter": voter_profile,
        "has_voted": has_voted,
        "is_running": is_running,
        "time_remaining": time_remaining_seconds,
        "candidates": candidates   # ✅ VERY IMPORTANT
    }

    return render(request, "voterapp/home.html", context)




# ---------------- VOTE ----------------
import random
import socket
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

from .models import Election, Candidate, Voter, Vote

logger = logging.getLogger(__name__)

@login_required
def vote(request):
    election = Election.objects.filter(is_active=True).first()

    if not election:
        messages.error(request, "❌ No active election available.")
        return redirect("home")

    if not election.is_running():
        messages.warning(request, "⏳ Voting is not open right now.")
        return redirect("home")

    voter_profile = Voter.objects.filter(user=request.user).first()

    if not voter_profile:
        messages.error(request, "Voter profile not found.")
        return redirect("home")

    if not voter_profile.is_approved:
        messages.error(request, "❌ Your account is not approved by admin.")
        return redirect("home")

    if Vote.objects.filter(voter=voter_profile, election=election).exists():
        return redirect("vote_receipt")

    candidates = Candidate.objects.filter(election=election)

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")

        try:
            candidate = Candidate.objects.get(id=candidate_id, election=election)
        except Candidate.DoesNotExist:
            messages.error(request, "Invalid candidate selection.")
            return redirect("vote")
        
        photo_data = request.POST.get("photo_data")
        request.session["photo_data"] = photo_data

        # ✅ Generate OTP ONLY ONCE
        otp = random.randint(100000, 999999)

        # Save OTP in session
        request.session['vote_otp'] = str(otp)
        request.session['candidate_id'] = candidate.id
        request.session['otp_time'] = str(timezone.now())
        request.session.modified = True

        print("OTP GENERATED:", otp)
        print("Sending to:", voter_profile.email)

        # ✅ Wrap network/email execution in a safe error block
        try:
            send_mail(
                "Voting OTP Verification",
                f"Your OTP for voting is: {otp}",
                "aaronpinheiro84@gmail.com",
                [voter_profile.email], 
                fail_silently=False,
            )
            messages.info(request, "📧 OTP sent to your registered email.")
            return redirect("verify_otp")

        except (socket.error, Exception) as e:
            logger.error(f"Network error when dispatching email to {voter_profile.email}: {e}")
            messages.error(
                request, 
                "❌ System was unable to send verification email. Please check your network or try again."
            )
            return redirect("vote")

    return render(request, "voterapp/vote.html", {
        "candidates": candidates,
        "election": election
    })

# ---------------- RESULTS ----------------
@login_required
def results(request):
    election = Election.objects.filter(is_active=True).first()

    if not election:
        messages.error(request, "No active election.")
        return redirect("home")

    vote_data = (
        Vote.objects
        .filter(election=election)
        .values('candidate__name', 'candidate__party')
        .annotate(vote_count=Count('id'))
        .order_by('-vote_count')
    )

    total_votes = Vote.objects.filter(election=election).count()

    results = []
    highest_votes = max([item['vote_count'] for item in vote_data], default=0)

    for item in vote_data:
        percentage = (
            round((item['vote_count'] / total_votes) * 100, 2)
            if total_votes > 0 else 0
        )

        results.append({
            'name': item['candidate__name'],
            'party': item['candidate__party'],
            'vote_count': item['vote_count'],
            'percentage': percentage,
            'is_winner': item['vote_count'] == highest_votes and highest_votes > 0
        })

    return render(request, 'voterapp/results.html', {
        'results': results,
        'total_votes': total_votes,
        'election': election
    })


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    voter_profile = Voter.objects.filter(user=request.user).first()
    return render(request, 'voterapp/profile.html', {'user': voter_profile})


# ---------------- LOGOUT ----------------
def logout(request):
    auth_logout(request)
    return redirect('index')



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Voter, Candidate, Election, Vote


from datetime import timedelta
from django.utils import timezone

@login_required
def verify_otp(request):

    session_otp = request.session.get("vote_otp")
    candidate_id = request.session.get("candidate_id")
    otp_time = request.session.get("otp_time")

    # Check session
    if not session_otp or not candidate_id or not otp_time:
        messages.error(request, "Session expired. Please vote again.")
        return redirect("vote")

    # Convert stored time
    otp_time = timezone.datetime.fromisoformat(otp_time)

    # Check expiry (2 minutes)
    if timezone.now() > otp_time + timedelta(minutes=2):
        request.session.pop("vote_otp", None)
        request.session.pop("candidate_id", None)
        request.session.pop("otp_time", None)

        messages.error(request, "⏰ OTP expired. Please vote again.")
        return redirect("vote")

    if request.method == "POST":

        entered_otp = request.POST.get("otp", "").strip()
        session_otp = str(session_otp).strip()

        print("ENTERED OTP:", entered_otp)
        print("SESSION OTP:", session_otp)

        if entered_otp != session_otp:
            messages.error(request, "❌ Invalid OTP")
            return redirect("verify_otp")

        try:
            voter = Voter.objects.get(user=request.user)
            election = Election.objects.filter(is_active=True).first()
            candidate = Candidate.objects.get(id=candidate_id)

            Vote.objects.create(
                voter=voter,
                candidate=candidate,
                election=election,
                voted_at=timezone.now()
            )

        except Exception as e:
            print("Vote Error:", e)
            messages.error(request, "Error while saving vote.")
            return redirect("vote")

        # Clear session
        request.session.pop("vote_otp", None)
        request.session.pop("candidate_id", None)
        request.session.pop("otp_time", None)

        messages.success(request, "🗳️ Vote successfully cast!")
        return redirect("vote_receipt")

    return render(request, "voterapp/verify_otp.html")

@login_required
def vote_receipt(request):
    voter = Voter.objects.get(user=request.user)
    election = Election.objects.filter(is_active=True).first()

    vote = Vote.objects.filter(voter=voter, election=election).first()

    if not vote:
        messages.error(request, "You have not voted yet.")
        return redirect("home")

    return render(request, "voterapp/vote_receipt.html", {
        "vote": vote,
        "voter": voter
    })


from datetime import datetime, date

def register(request):

    if request.method == "POST":

        dob = request.POST.get("dob")
        dob = datetime.strptime(dob, "%Y-%m-%d").date()

        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 18:
            messages.error(request, "You must be at least 18 years old.")
            return redirect("register")

        # your existing user save code continues here

from .models import Voter, Vote
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin, login_url='home')
def admin_dashboard(request):
    total_voters = Voter.objects.count()
    approved_voters = Voter.objects.filter(is_approved=True).count()
    pending_voters = Voter.objects.filter(is_approved=False).count()
    total_votes = Vote.objects.count()

    context = {
        "total_voters": total_voters,
        "approved_voters": approved_voters,
        "pending_voters": pending_voters,
        "total_votes": total_votes,
    }

    return render(request, "voterapp/admin_dashboard.html", context)

from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    send_mail(
        "Test Email",
        "This is a test email from Django",
        "aaronpinheiro84@gmail.com",
        ["aaronpinheiro84@gmail.com"],
        fail_silently=False,
    )
    return HttpResponse("Email Sent")
