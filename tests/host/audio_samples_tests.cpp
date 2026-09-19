#include "../../src/audio_samples.h"
#include <cassert>
#include <iostream>
int main() {
    assert(AudioSamples::music(0,0)==0);
    assert(AudioSamples::music(32767,32767)==2147418112);
    assert(AudioSamples::music(-32768,-32768)==-2147483648);
    assert(AudioSamples::music(20000,-20000)==0);
    assert(AudioSamples::voice(127)==2130706432);
    assert(AudioSamples::voice(-128)==-2147483648);
    assert(AudioSamples::voice(0)==0);
    for(int sample=-128;sample<127;++sample)
        assert(AudioSamples::voice((int8_t)sample)<AudioSamples::voice((int8_t)(sample+1)));
    AudioSamples::volumePercent.store(50);
    assert(AudioSamples::music(32767,32767)==1073709056);
    assert(AudioSamples::voice(-128)==-1073741824);
    assert(AudioSamples::volume(INT32_MIN)==-1073741824);
    AudioSamples::volumePercent.store(25);
    assert(AudioSamples::volume(INT32_MIN)==-536870912);
    AudioSamples::volumePercent.store(100);
    assert(AudioSamples::volume(INT32_MIN)==INT32_MIN);
    std::cout << "PASS: audio conversion and volume scaling without overflow\n";
}
