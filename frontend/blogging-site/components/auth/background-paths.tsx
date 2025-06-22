'use client';

export function BackgroundPaths() {
    const paths = Array.from({ length: 20 }).map((_, i) => ({
        d: `M-246.655 ${1120.8 - i * 30}C-246.655 ${1120.8 - i * 30} -469.655 ${997.8 - i * 30} 21.3453 ${997.8 - i * 30}C512.345 ${997.8 - i * 30} 424.345 ${759.8 - i * 30} 864.345 ${759.8 - i * 30}C1304.35 ${759.8 - i * 30} 1529.35 ${532.8 - i * 30} 1221.35 ${532.8 - i * 30}C913.345 ${532.8 - i * 30} 921.345 ${253.8 - i * 30} 501.345 ${253.8 - i * 30}C81.3453 ${253.8 - i * 30} -161.655 ${1.80005 - i * 30} -161.655 ${1.80005 - i * 30}`,
        delay: i * -0.5,
    }));

    return (
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
            <div className="absolute w-[100%] h-[123%] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                <svg
                    className="absolute w-full h-full"
                    width="1440"
                    height="810"
                    viewBox="0 0 1440 810"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    preserveAspectRatio="xMidYMid slice"
                >
                    <g clipPath="url(#clip0_1_2)">
                        {paths.map((path, index) => (
                            <path
                                key={index}
                                d={path.d}
                                stroke={`url(#paint${index}_linear_1_2)`}
                                strokeWidth="2"
                                className="path-anim"
                                style={{ animationDelay: `${path.delay}s` }}
                                filter="url(#glow)"
                            />
                        ))}
                    </g>
                    <defs>
                        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="3.5" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                        <clipPath id="clip0_1_2">
                            <rect width="1440" height="810" fill="white" />
                        </clipPath>
                        {paths.map((_, index) => (
                            <linearGradient
                                key={index}
                                id={`paint${index}_linear_1_2`}
                                x1="683.5"
                                y1="-50.5"
                                x2="683.5"
                                y2="1000.5"
                                gradientUnits="userSpaceOnUse"
                            >
                                <stop stopColor="#FFFFFF" stopOpacity="0.6" />
                                <stop offset="1" stopColor="#FFFFFF" stopOpacity="0" />
                            </linearGradient>
                        ))}
                    </defs>
                </svg>
            </div>
            <style jsx>{`
                .path-anim {
                    animation: path-anim 10s linear infinite;
                }

                @keyframes path-anim {
                    0% {
                        stroke-dasharray: 1000;
                        stroke-dashoffset: 1000;
                    }
                    100% {
                        stroke-dasharray: 1000;
                        stroke-dashoffset: -1000;
                    }
                }
            `}</style>
        </div>
    );
}
