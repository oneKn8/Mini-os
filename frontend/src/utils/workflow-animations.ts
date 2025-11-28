import gsap from 'gsap';

export interface AnimationConfig {
  duration?: number;
  ease?: string;
  delay?: number;
  stagger?: number;
}

export const defaultAnimationConfig: AnimationConfig = {
  duration: 0.5,
  ease: 'power2.out',
  delay: 0,
  stagger: 0.1,
};

export const workflowAnimations = {
  pulseNode: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 1, ease = 'sine.inOut' } = config;

    return gsap.to(element, {
      scale: 1.1,
      opacity: 0.8,
      duration,
      ease,
      yoyo: true,
      repeat: -1,
    });
  },

  highlightNode: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.3, ease = 'power2.out' } = config;

    return gsap.timeline()
      .to(element, {
        scale: 1.2,
        duration,
        ease,
      })
      .to(element, {
        scale: 1,
        duration,
        ease,
      });
  },

  fadeIn: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', delay = 0 } = config;

    return gsap.from(element, {
      opacity: 0,
      duration,
      ease,
      delay,
    });
  },

  fadeInUp: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', delay = 0 } = config;

    return gsap.from(element, {
      opacity: 0,
      y: 20,
      duration,
      ease,
      delay,
    });
  },

  staggerFadeIn: (elements: (HTMLElement | SVGElement)[], config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', stagger = 0.1 } = config;

    return gsap.from(elements, {
      opacity: 0,
      y: 10,
      duration,
      ease,
      stagger,
    });
  },

  drawPath: (pathElement: SVGPathElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 1, ease = 'power1.inOut', delay = 0 } = config;

    const length = pathElement.getTotalLength();

    return gsap.fromTo(
      pathElement,
      {
        strokeDasharray: length,
        strokeDashoffset: length,
      },
      {
        strokeDashoffset: 0,
        duration,
        ease,
        delay,
      }
    );
  },

  animateParticle: (
    element: SVGElement,
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
    config: Partial<AnimationConfig> = {}
  ) => {
    const { duration = 2, ease = 'power1.inOut', delay = 0 } = config;

    return gsap.timeline({ repeat: -1, repeatDelay: 1 })
      .set(element, { x: fromX, y: fromY, opacity: 0 })
      .to(element, {
        opacity: 1,
        duration: duration * 0.1,
        delay,
      })
      .to(element, {
        x: toX,
        y: toY,
        duration: duration * 0.8,
        ease,
      })
      .to(element, {
        opacity: 0,
        duration: duration * 0.1,
      });
  },

  scaleIn: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'back.out(1.7)', delay = 0 } = config;

    return gsap.from(element, {
      scale: 0,
      opacity: 0,
      duration,
      ease,
      delay,
    });
  },

  rotateIn: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', delay = 0 } = config;

    return gsap.from(element, {
      rotation: -180,
      opacity: 0,
      duration,
      ease,
      delay,
    });
  },

  shakeNode: (element: HTMLElement | SVGElement) => {
    return gsap.timeline()
      .to(element, {
        x: -5,
        duration: 0.1,
        ease: 'power1.inOut',
      })
      .to(element, {
        x: 5,
        duration: 0.1,
        ease: 'power1.inOut',
      })
      .to(element, {
        x: -5,
        duration: 0.1,
        ease: 'power1.inOut',
      })
      .to(element, {
        x: 0,
        duration: 0.1,
        ease: 'power1.inOut',
      });
  },

  successFlash: (element: HTMLElement | SVGElement) => {
    const tl = gsap.timeline();

    tl.to(element, {
      backgroundColor: '#10b981',
      duration: 0.2,
      ease: 'power2.out',
    })
      .to(element, {
        scale: 1.1,
        duration: 0.2,
        ease: 'back.out(2)',
      })
      .to(element, {
        scale: 1,
        duration: 0.2,
        ease: 'power2.inOut',
      });

    return tl;
  },

  errorFlash: (element: HTMLElement | SVGElement) => {
    const tl = gsap.timeline();

    tl.to(element, {
      backgroundColor: '#ef4444',
      duration: 0.2,
      ease: 'power2.out',
    })
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .call(() => workflowAnimations.shakeNode(element) as any)
      .to(element, {
        duration: 0.3,
      });

    return tl;
  },

  morphPath: (
    pathElement: SVGPathElement,
    fromPath: string,
    toPath: string,
    config: Partial<AnimationConfig> = {}
  ) => {
    const { duration = 1, ease = 'power2.inOut', delay = 0 } = config;

    return gsap.fromTo(
      pathElement,
      { attr: { d: fromPath } },
      {
        attr: { d: toPath },
        duration,
        ease,
        delay,
      }
    );
  },

  createTimeline: (config: Partial<AnimationConfig> = {}) => {
    return gsap.timeline(config);
  },

  killAll: () => {
    gsap.killTweensOf('*');
  },

  progressBar: (element: HTMLElement, percent: number, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out' } = config;

    return gsap.to(element, {
      width: `${percent}%`,
      duration,
      ease,
    });
  },

  numberCounter: (element: HTMLElement, from: number, to: number, config: Partial<AnimationConfig> = {}) => {
    const { duration = 1, ease = 'power1.out' } = config;

    const obj = { value: from };

    return gsap.to(obj, {
      value: to,
      duration,
      ease,
      onUpdate: () => {
        element.textContent = Math.round(obj.value).toString();
      },
    });
  },

  flowParticles: (
    container: SVGElement,
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
    count: number = 3,
    config: Partial<AnimationConfig> = {}
  ) => {
    const particles: SVGCircleElement[] = [];
    const tl = gsap.timeline({ repeat: -1 });

    for (let i = 0; i < count; i++) {
      const particle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      particle.setAttribute('r', '3');
      particle.setAttribute('fill', '#60a5fa');
      container.appendChild(particle);
      particles.push(particle);

      tl.add(workflowAnimations.animateParticle(
        particle,
        fromX,
        fromY,
        toX,
        toY,
        { ...config, delay: i * 0.5 }
      ), 0);
    }

    return {
      timeline: tl,
      cleanup: () => {
        tl.kill();
        particles.forEach((p) => p.remove());
      },
    };
  },

  ripple: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 1, ease = 'power1.out' } = config;

    const ripple = document.createElement('div');
    ripple.className = 'absolute rounded-full border-2 border-blue-400 opacity-75';
    ripple.style.width = '100%';
    ripple.style.height = '100%';
    ripple.style.top = '0';
    ripple.style.left = '0';

    const parent = element instanceof SVGElement ? element.parentElement : element;
    parent?.appendChild(ripple);

    return gsap.to(ripple, {
      scale: 2,
      opacity: 0,
      duration,
      ease,
      onComplete: () => ripple.remove(),
    });
  },

  bounce: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'bounce.out', delay = 0 } = config;

    return gsap.from(element, {
      y: -20,
      duration,
      ease,
      delay,
    });
  },

  slideInFromRight: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', delay = 0 } = config;

    return gsap.from(element, {
      x: 100,
      opacity: 0,
      duration,
      ease,
      delay,
    });
  },

  slideInFromLeft: (element: HTMLElement | SVGElement, config: Partial<AnimationConfig> = {}) => {
    const { duration = 0.5, ease = 'power2.out', delay = 0 } = config;

    return gsap.from(element, {
      x: -100,
      opacity: 0,
      duration,
      ease,
      delay,
    });
  },
};

export default workflowAnimations;
