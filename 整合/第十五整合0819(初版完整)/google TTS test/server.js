const express = require('express');
const textToSpeech = require('@google-cloud/text-to-speech');
const cors = require('cors');
const app = express();
const path = require('path');

app.use(cors());
app.use(express.json());

const client = new textToSpeech.TextToSpeechClient({
  keyFilename: path.join(__dirname, 'google TTS test', 'gold-hold.json') // 替換為你的 JSON 憑證文件路徑
});

app.post('/synthesize', async (req, res) => {
  const text = req.body.text;
  const voice = req.body.voice || 'cmn-TW-Wavenet-A';
  const speakingRate = req.body.speakingRate || 0.80;  // 語速
  const pitch = req.body.pitch || 0.10;               // 音調
  const volumeGainDb = req.body.volumeGainDb || 0.0; // 音量增益
  const effectsProfileId = req.body.effectsProfileId || 'headphone-class-device'; // 音效配置檔案

  const request = {
    input: { text },
    voice: { languageCode: 'cmn-TW', name: voice },
    audioConfig: { 
      audioEncoding: 'MP3',
      speakingRate: speakingRate,
      pitch: pitch,
      volumeGainDb: volumeGainDb,
      effectsProfileId: effectsProfileId ? [effectsProfileId] : []
    },
  };

  try {
    const [response] = await client.synthesizeSpeech(request);
    res.set('Content-Type', 'audio/mpeg');
    res.send(response.audioContent);
  } catch (error) {
    console.error('Error synthesizing speech:', error);
    res.status(500).send('Error synthesizing speech');
  }
});

app.listen(3000, () => {
  console.log('Server is running on port 3000');
});
