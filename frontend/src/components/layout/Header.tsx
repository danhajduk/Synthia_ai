import { useEffect, useState } from "react";
import { getGreeting } from "../../utils/getGreeting";

const Header = () => {
  const [greeting, setGreeting] = useState(getGreeting());

  useEffect(() => {
    const timer = setInterval(() => {
      setGreeting(getGreeting());
    }, 600_000); // check every minute

    return () => clearInterval(timer);
  }, []);

  return (
    <header className="app-header">
      <div className="app-header-left">
        <span className="app-header-label">
          {greeting}, Dan
        </span>

        <span className="app-header-title">
          Systems nominal. No fires… yet.
        </span>
      </div>

      <div className="app-header-right">
        <span className="app-header-ip">10.0.0.100</span>
        <div className="app-header-avatar" />
      </div>
    </header>
  );
};

export default Header;
