export const theme = {
  glass: {
    light: 'bg-white/40 backdrop-blur-3xl border border-white/60 shadow-liquid-glass',
    heavy: 'bg-white/80 backdrop-blur-3xl border border-white/60 shadow-[0_40px_80px_rgba(0,91,192,0.15)]',
    dark: 'bg-slate-900/40 backdrop-blur-3xl border border-white/10 shadow-2xl',
  },
  shadows: {
    liquid: 'shadow-liquid-glass',
    floating: 'shadow-[0_50px_100px_rgba(0,0,0,0.15)]',
  },
  animations: {
    spring: { type: "spring", damping: 25, stiffness: 400 },
    bounce: { type: "spring", damping: 15, stiffness: 300 },
  },
  borderRadius: {
    card: 'rounded-[2.5rem]',
    input: 'rounded-[1.5rem]',
    button: 'rounded-2xl',
  }
};
