const paths:Record<string,string>={
 '/dashboard':'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
 '/receipts':'M6 3h12v18l-3-2-3 2-3-2-3 2z M9 7h6 M9 11h6',
 '/upload':'M12 5v14 M5 12h14',
 '/finances':'M3 7h18v13H3z M3 7l14-4v4 M16 12h5v4h-5z',
 '/more':'M5 12h.01 M12 12h.01 M19 12h.01',
 '/notifications':'M6 8a6 6 0 0 1 12 0v7l2 2H4l2-2z M9 20h6',
 '/logout':'M9 3H4v18h5 M10 12h11 M17 8l4 4-4 4',
 '/settings':'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2',
};
export default function NavIcon({href,className='h-5 w-5'}:{href:string;className?:string}){
 return <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[href]??'M5 4h14v16H5z M8 8h8 M8 12h8 M8 16h5'}/></svg>;
}
