#include <stdio.h>
#include "pico/stdlib.h"

#if __cplusplus < 202100L
#error This code requires C++23 or later
#endif

class Hello {
public:
    void say() {
        printf("Hello, world! %ld\n", __cplusplus);
    }
};

int main() {
    stdio_init_all();

    Hello hello;
    while (true) {
        hello.say();
        sleep_ms(1000);
    }
}
