#include <stdio.h>
__attribute__((noinline)) int CalculateDamage(int base_damage, int armor) {
    if (base_damage <= 0) return 0;
    int result = base_damage - armor;
    return result > 1 ? result : 1;
}
int main(void) {
    int result=CalculateDamage(75,25);
    printf("Damage=%d\n",result);
    return result==50?0:1;
}
