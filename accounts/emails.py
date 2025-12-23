# accounts/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def send_password_reset_email(user, request):
    """Send a password reset email to the user with HTML support."""
    subject = "Password Reset Request - Electronic Shop"

    # Prepare context for the email templates
    context = {
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',
    }

    # Render HTML content
    html_content = render_to_string('emails/password_reset_email.html', context)

    # Create plain text version (fallback for email clients that don't support HTML)
    text_content = f"""\
    Hello,

    You're receiving this email because you requested a password reset for your Electronic Shop account.

    Please go to the following page and choose a new password:
    {context['protocol']}://{context['domain']}/accounts/reset/{context['uid']}/{context['token']}/

    If you didn't request this, please ignore this email.

    This link will expire in 24 hours.

    Thanks,
    The Electronic Shop Team
    """

    # Create email message with both HTML and plain text versions
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()