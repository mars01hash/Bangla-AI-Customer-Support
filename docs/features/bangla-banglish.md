# Bangla & Banglish Support

The platform is designed from the ground up for Bangladeshi users who naturally mix Bangla script, English words, and Banglish (Bangla grammar with English vocabulary) in the same message.

## Language Detection

Every message is classified before routing:

| Detected | Condition |
|---|---|
| `bn` (Bangla) | Contains Bangla Unicode characters (`U+0980–U+09FF`), no English words |
| `en` (English) | No Bangla characters |
| `mixed` | Both Bangla characters and English words present |

The detected language is stored in `AgentState.detected_language` and passed to every node, which uses it to choose the response language.

## Language Toggle

The chat widget includes a **Bangla / English toggle** button. When the user selects a language, the preference is sent with every subsequent message as `preferred_language`. This overrides the auto-detected language:

```python
lang = preferred if preferred in ("bn", "en") else detect_language_heuristics(current_message)
```

## Banglish Intent Recognition

Bangladeshi users commonly write Banglish in chat — English words with Bangla verb endings. The intent classifier covers these patterns:

| Banglish phrase | Meaning | Recognised as |
|---|---|---|
| `order korbo` | I will order | buy intent + affirmative |
| `kinbo` | I will buy | buy intent |
| `order debo` | I will place an order | buy intent |
| `korbo` | I will do it | affirmative |
| `nebo` | I will take it | affirmative |
| `debo` | I will give | affirmative |

## Sentiment Keywords

Sentiment detection also covers Bangla:

| Sentiment | Bangla keywords |
|---|---|
| Negative | `খারাপ`, `বাজে`, `পচা`, `ভুল`, `সমস্যা`, `দেরি`, `হতাশ`, `ফালতু` |
| Positive | `ভালো`, `সুন্দর`, `ধন্যবাদ`, `সেরা`, `দুর্দান্ত`, `অসাধারণ` |

## Response Language

All agent nodes generate responses in the detected language. The LLM system prompt always includes `Language: {lang}`. For heuristic fallbacks (when LLM is disabled or fails), each node has hardcoded responses in both Bangla and English.
