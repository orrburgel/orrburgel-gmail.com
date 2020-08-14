var animStars = lottie.loadAnimation(animStarsData);

import OnScreen from 'onscreen';
const os = new OnScreen();

os.on('enter', '#stars', (element, event) => {
    animStars.play();
});
os.on('leave', ''#stars', (element, event) => {
    animStars.goToAndStop(0);
});
