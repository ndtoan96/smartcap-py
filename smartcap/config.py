import json
from pathlib import Path


class ConfigValues(object):
    def __init__(self):
        self.path = Path.home().joinpath(".smartcap/config.json")
        if self.path.exists():
            data = json.load(open(self.path, "r"))
            self.provider = data["provider"]
            self.model = data["model"]
            self.apiKey = data["api-key"]
            self.systemPrompt = data["system-prompt"]
        else:
            self.provider = "Google"
            self.model = "gemini-2.0-flash"
            self.apiKey = ""
            self.systemPrompt = "You are a helpful assistant"
            self.path.parent.mkdir(parents=True)
            self.save()

    def setProvider(self, provider: str):
        self.provider = provider
        self.save()

    def setModel(self, model: str):
        self.model = model
        self.save()

    def setApiKey(self, apiKey: str):
        self.apiKey = apiKey
        self.save()

    def setSystemPrompt(self, systemPrompt: str):
        self.systemPrompt = systemPrompt
        self.save()

    def save(self):
        data = {
            "provider": self.provider,
            "model": self.model,
            "api-key": self.apiKey,
            "system-prompt": self.systemPrompt,
        }
        json.dump(data, open(self.path, "w"))
