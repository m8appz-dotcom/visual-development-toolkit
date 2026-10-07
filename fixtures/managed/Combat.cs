namespace ModdingLab.Fixture;
public static class Combat {
    public static int CalculateDamage(int baseDamage,int armor) {
        if(baseDamage<=0)return 0;
        return Math.Max(1,baseDamage-armor);
    }
}
