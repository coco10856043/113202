const express = require('express');
const textToSpeech = require('@google-cloud/text-to-speech');
const cors = require('cors');
const app = express();
const path = require('path');

// 使用环境变量配置凭据（可选）
process.env.GOOGLE_APPLICATION_CREDENTIALS = path.join(__dirname, 'gold-hold.json');

app.use(cors());
app.use(express.json());

const client = new textToSpeech.TextToSpeechClient();

app.post('/synthesize', async (req, res) => {
  const text = req.body.text;
  const voice = req.body.voice || 'cmn-TW-Wavenet-A';
  const speakingRate = req.body.speakingRate || 0.80;  // 语速
  const pitch = req.body.pitch || 0.10;               // 音调
  const volumeGainDb = req.body.volumeGainDb || 0.0; // 音量增益
  const effectsProfileId = req.body.effectsProfileId || 'headphone-class-device'; // 音效配置文件

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

app.listen(3001, '140.131.114.151', () => {
  console.log('Server is running on port 3001');
});
