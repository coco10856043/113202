const express = require('express');
const textToSpeech = require('@google-cloud/text-to-speech');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

try {
  const client = new textToSpeech.TextToSpeechClient({
    keyFilename: 'C:\\Users\\88696\\Desktop\\北商資管\\二技專題\\第十一整合0802\\gold-hold.json'
  });
} catch (error) {
  console.error('Failed to initialize TextToSpeechClient:', error.message);
}


app.post('/synthesize', async (req, res) => {
  const text = req.body.text;
  const voice = req.body.voice || 'cmn-TW-Wavenet-A';

  console.log(`Received text: ${text}`);
  console.log(`Using voice: ${voice}`);

  const request = {
    input: { text },
    voice: { languageCode: 'cmn-TW', name: voice },
    audioConfig: { audioEncoding: 'MP3' },
  };

  try {
    const [response] = await client.synthesizeSpeech(request);
    console.log('Speech synthesized successfully');
    res.set('Content-Type', 'audio/mpeg');
    res.send(response.audioContent);
  } catch (error) {
    console.error('Error synthesizing speech:', error.message);
    if (error.response) {
      console.error('API Response Error:', error.response.data);
    } else {
      console.error('Unexpected Error:', error);
    }
    res.status(500).send('Error synthesizing speech');
  }
});



app.listen(3000, () => {
  console.log('Server is running on port 3000');
});
