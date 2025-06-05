# XAgent Twitter Integration

This document describes the integrated Twitter functionality within XAgent, providing seamless browser-based Twitter automation.

## Features

### 🎭 Stealth Browser Automation
- Patchright stealth browser with enhanced anti-detection
- Advanced fingerprint resistance
- Bypasses major bot detection systems

### 🐦 Twitter Capabilities
- **Tweet Creation**: Post tweets with optional media and persona-based content generation
- **Reply Management**: Reply to tweets with context-aware responses
- **User Following**: Follow individual users or bulk follow multiple users
- **List Management**: Create and manage Twitter lists
- **Persona System**: Use different personas for varied content styles

### 🔐 Secure Credential Management
- Encrypted storage of Twitter credentials
- TOTP (Two-Factor Authentication) support
- Profile-based configuration isolation
- Cookie-based authentication support

### ⏱️ Behavioral Loops & Scheduling
- Configure automated action sequences
- Time-based triggers and intervals
- Complex action workflows
- Profile-specific loop configurations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Clone and Install twagent

```bash
git clone https://github.com/lord-dubious/twagent
cd twagent
pip install -e .
```

### 3. Configure Twitter Authentication

#### Option A: Using Credentials (Recommended)
1. Go to the XAgent tab in the web UI
2. Navigate to "🐦 Twitter Actions"
3. Fill in your Twitter credentials:
   - Username
   - Email
   - Password
   - TOTP Secret (for 2FA)
4. Click "💾 Save Credentials"

#### Option B: Using Cookies
1. Export your Twitter cookies from your browser
2. Save them as `cookies.json` in the root directory
3. Use the format shown in `cookies.example.json`

### 4. Set Up Personas (Optional)

Create persona files in the `personas/` directory:

```json
{
  "name": "tech_enthusiast",
  "description": "A technology enthusiast who loves AI and automation",
  "personality": {
    "tone": "enthusiastic",
    "style": "informative",
    "interests": ["AI", "automation", "technology"],
    "hashtags": ["#AI", "#automation", "#tech"]
  },
  "tweet_templates": [
    "Just discovered an amazing new {topic}! 🚀 {content} #tech"
  ]
}
```

## Usage

### Basic Twitter Actions

1. **Initialize Twitter**: Click "🚀 Initialize Twitter" in the Twitter Actions tab
2. **Create Tweet**: Enter content and optionally select a persona
3. **Reply to Tweet**: Provide tweet URL and reply content
4. **Follow Users**: Enter username or bulk follow multiple users

### Behavioral Loops

Configure automated actions in the "⏱️ Behavioral Loops" tab:

```json
[
  {
    "id": "daily_engagement",
    "description": "Daily Twitter engagement routine",
    "interval_seconds": 3600,
    "actions": [
      {
        "type": "tweet",
        "params": {
          "content": "Good morning Twitter! 🌅",
          "persona": "tech_enthusiast"
        }
      },
      {
        "type": "delay",
        "params": {
          "seconds": 300
        }
      },
      {
        "type": "follow",
        "params": {
          "username": "openai"
        }
      }
    ]
  }
]
```

### Profile Management

- **Switch Profiles**: Use the profile dropdown to switch between different configurations
- **Create Profiles**: Each profile has isolated credentials and settings
- **Export/Import**: Profiles are stored as JSON files in the `profiles/` directory

## Action Types

### Tweet Actions
- `tweet`: Create a new tweet
- `reply`: Reply to an existing tweet

### User Actions
- `follow`: Follow a single user
- `bulk_follow`: Follow multiple users

### Utility Actions
- `delay`: Wait for specified seconds
- `create_list`: Create a Twitter list

## Security Features

### Credential Encryption
- All sensitive data is encrypted using Fernet (AES 128)
- Profile-specific encryption keys
- TOTP secrets are securely stored

### Browser Stealth
- Patchright browser with Runtime.enable patched
- Console.enable patched for stealth
- Enhanced anti-detection measures
- Closed shadow root interaction support

## Configuration Files

### Profile Configuration (`profiles/{profile_name}/config.json`)
```json
{
  "twitter": {
    "cookies_path": "./cookies.json",
    "persona_path": "./personas"
  },
  "credentials": {
    "username": "encrypted_username",
    "email": "encrypted_email", 
    "password": "encrypted_password",
    "totp_secret": "encrypted_totp_secret"
  },
  "action_loops": [...],
  "scheduled_actions": [...]
}
```

### Persona Configuration (`personas/{persona_name}.json`)
```json
{
  "name": "persona_name",
  "description": "Persona description",
  "personality": {
    "tone": "enthusiastic",
    "style": "informative",
    "interests": ["topic1", "topic2"],
    "hashtags": ["#tag1", "#tag2"]
  },
  "tweet_templates": [...],
  "reply_templates": [...]
}
```

## API Reference

### XAgent Twitter Methods

```python
# Create tweet
result = await xagent.create_tweet(
    content="Hello Twitter!",
    media_paths=["image.jpg"],
    persona_name="tech_enthusiast"
)

# Reply to tweet
result = await xagent.reply_to_tweet(
    tweet_url="https://twitter.com/user/status/123",
    content="Great point!",
    persona_name="tech_enthusiast"
)

# Follow user
result = await xagent.follow_user("username")

# Bulk follow
result = await xagent.bulk_follow(["user1", "user2", "user3"])

# Start behavioral loops
result = await xagent.start_action_loop()

# Stop behavioral loops
result = await xagent.stop_action_loop()
```

## Troubleshooting

### Common Issues

1. **Twitter not initializing**
   - Check credentials are correctly saved
   - Verify cookies.json format if using cookie authentication
   - Ensure twagent is properly installed

2. **TOTP codes not working**
   - Verify TOTP secret is correctly entered
   - Check system time is synchronized
   - Ensure secret is in base32 format

3. **Browser detection**
   - XAgent uses advanced stealth techniques
   - If detected, try different timing intervals
   - Consider using different personas for variety

### Logs and Debugging

- Check browser console for detailed error messages
- Enable debug logging in the XAgent configuration
- Monitor the Twitter Agent Log in the Results tab

## Best Practices

### Responsible Usage
1. Respect Twitter's Terms of Service
2. Use realistic timing intervals between actions
3. Vary content and behavior patterns
4. Monitor for rate limiting

### Security
1. Use strong, unique passwords
2. Enable 2FA on your Twitter account
3. Regularly rotate credentials
4. Keep profiles and configurations secure

### Performance
1. Use appropriate delays between actions
2. Monitor system resources during automation
3. Configure reasonable loop intervals
4. Test with small batches before bulk operations

## Contributing

To contribute to the Twitter integration:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This integration follows the same license as the main xv-ui project.

