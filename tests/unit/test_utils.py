# 3rd Party
from preggy import expect

# Fastlane
from fastlane.utils import words_redacted


def test_words_redacted(client):
    envs = {
        "_id": "5c93dcb40106107dc30efdd9",
        "clientSecret": "secret",
        "client": {
            "key": "key",
            "secret": "secret",
            "other": {
                "PASSWORD_ENV": "password"
            }
        },
    }

    blacklist_words_fn = client.application.blacklist_words_fn
    envs_redacted = words_redacted(envs, blacklist_words_fn)

    envs_expect = {
        "_id": "5c93dcb40106107dc30efdd9",
        "clientSecret": "***",
        "client": {
            "key": "***",
            "secret": "***",
            "other": {
                "PASSWORD_ENV": "***"
            },
        }
    }
    expect(envs_redacted).to_be_like(envs_expect)


def test_words_redacted2(client):
    envs_orig = {
        "client_id": "40106107dc30efdd9",
        "name": "noneoneoneo",
        "Key": "key",
    }

    envs = {
        "client_id": "40106107dc30efdd9",
        "name": "noneoneoneo",
        "Key": "key",
    }

    blacklist_words_fn = client.application.blacklist_words_fn
    replacements = "###"
    envs_redacted = words_redacted(envs, blacklist_words_fn, replacements)

    envs_expect = {
        "client_id": "###",
        "name": "noneoneoneo",
        "Key": "###",
    }

    expect(envs).to_be_like(envs_orig)
    expect(envs_redacted).to_be_like(envs_expect)
