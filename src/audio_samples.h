#pragma once
#include <stdint.h>
#include <atomic>

namespace AudioSamples {
inline std::atomic<int> volumePercent{100};
inline int32_t volume(int32_t sample) {
    return (int32_t)((int64_t)sample * volumePercent.load() / 100);
}
// Full-scale PCM mapping; the user volume setting still applies.
inline int32_t music(int16_t left, int16_t right) {
    return volume(((int32_t(left) + int32_t(right)) / 2) * 65536);
}
inline int32_t voice(int8_t sample) {
    return volume(int32_t(sample) * 16777216);
}
}
