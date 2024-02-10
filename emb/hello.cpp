#include <stdio.h>
#include "pb_encode.h"
#include "pb_decode.h"
#include "pico/stdlib.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

#include "emb/hello.pb.h"

class Hello {
public:
    void say(const emb_Config& config) {
        printf("Hello, world! %ld\n", config.ping);
        // printf("Hello, world! %ld\n", __cplusplus);
    }
};

int main() {
    stdio_init_all();

    emb_Config config = emb_Config_init_default;

    Hello hello;
    while (true) {
        hello.say(config);
        config.ping++;
        sleep_ms(1000);
    }
}
