#!/usr/bin/env python3
"""
Test Email Functionality
Run this to verify SMTP is working correctly
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from email_service import email_service

async def send_test_email():
    """Send a test email to verify SMTP configuration"""
    
    test_email = "amarktainetwork@gmail.com"
    
    print("=" * 70)
    print("AMARKTAI NETWORK - EMAIL TEST")
    print("=" * 70)
    print(f"\nSending test email to: {test_email}")
    print(f"SMTP Host: {email_service.smtp_host}")
    print(f"SMTP Port: {email_service.smtp_port}")
    print(f"SMTP User: {email_service.smtp_user}")
    print("-" * 70)
    
    # Test email HTML
    subject = "🎉 Amarktai Network - Email System Test"
    
    html_body = """
    <html>
    <head>
        <style>
            body { margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #000010 0%, #00002a 100%); }
            .header { background: linear-gradient(135deg, #002b57 0%, #10b981 100%); padding: 40px 30px; text-align: center; }
            .header h1 { margin: 0; color: #ffffff; font-size: 28px; }
            .content { padding: 30px; color: #ffffff; }
            .success-box { background: rgba(16, 185, 129, 0.1); border: 2px solid #10b981; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }
            .success-icon { font-size: 48px; margin-bottom: 10px; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
            .info-card { background: #001a33; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 15px; text-align: center; }
            .info-label { color: #b3b3b3; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }
            .info-value { color: #10b981; font-size: 20px; font-weight: 700; }
            .footer { background: #000010; padding: 20px; text-align: center; color: #666; font-size: 12px; }
            .btn { display: inline-block; background: #10b981; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Amarktai Network</h1>
                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">AI-Powered Autonomous Crypto Trading</p>
            </div>
            
            <div class="content">
                <div class="success-box">
                    <div class="success-icon">✅</div>
                    <h2 style="margin: 10px 0; color: #10b981;">Email System Active!</h2>
                    <p style="margin: 10px 0; color: #b3b3b3;">SMTP configuration successful</p>
                </div>
                
                <h3 style="color: #10b981;">Test Details:</h3>
                
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">Status</div>
                        <div class="info-value">✓ Working</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Server</div>
                        <div class="info-value">Gmail</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">From</div>
                        <div class="info-value" style="font-size: 11px;">amarktainetwork@gmail.com</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Encryption</div>
                        <div class="info-value">TLS</div>
                    </div>
                </div>
                
                <p style="margin-top: 30px;">Your email system is now ready to send:</p>
                <ul style="color: #b3b3b3; line-height: 1.8;">
                    <li>📊 Daily trading reports (8 AM & 6 PM)</li>
                    <li>🎯 Trade execution alerts</li>
                    <li>📈 Weekly performance summaries</li>
                    <li>🤖 AI learning insights</li>
                    <li>⚠️ Critical system notifications</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="https://amarktai.online" class="btn">Go to Dashboard</a>
                </div>
            </div>
            
            <div class="footer">
                <p style="margin: 0 0 10px 0;"><strong>Amarktai Network</strong></p>
                <p style="margin: 0;">Growing Your Wealth 24/7 with AI Technology</p>
                <p style="margin: 10px 0 0 0;">📧 amarktainetwork@gmail.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        success = await email_service.send_email(
            to_email=test_email,
            subject=subject,
            body=html_body,
            html=True
        )
        
        if success:
            print("\n✅ SUCCESS! Test email sent successfully!")
            print(f"✓ Check inbox: {test_email}")
            print("\nSMTP Configuration: WORKING")
        else:
            print("\n❌ FAILED! Could not send test email")
            print("Check SMTP password and settings")
        
        print("=" * 70)
        return success
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("=" * 70)
        return False

if __name__ == "__main__":
    result = asyncio.run(send_test_email())
    sys.exit(0 if result else 1)
