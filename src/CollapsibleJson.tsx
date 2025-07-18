import React, { useState } from 'react';

interface CollapsibleNodeProps {
  name?: string | number;
  data: any;
  depth?: number;
}

const INDENT_SIZE = 3; // remove indentation

const CollapsibleNode: React.FC<CollapsibleNodeProps> = ({ name, data, depth = 0 }) => {
  const [open, setOpen] = useState(
    depth === 0 || 
    name === 'parameters' || 
    (typeof name === 'number' && depth >= 1) // auto-expand array indices
  ); // root, parameter nodes, and array indices open by default

  const isObject = typeof data === 'object' && data !== null;
  const isArray = Array.isArray(data);

  // Primitive leaf node rendering
  if (!isObject) {
    return (
      <div className="json-leaf" style={{ paddingLeft: depth * INDENT_SIZE }}>
        {name !== undefined && <span className="json-key">{String(name)}: </span>}
        <span className="json-value">{String(data)}</span>
      </div>
    );
  }

  const toggle = () => setOpen(!open);

  const childKeys = isArray ? data.map((_v: any, idx: number) => idx) : Object.keys(data);

  return (
    <div className="json-node" style={{ paddingLeft: depth * INDENT_SIZE }}>
      <div className="json-node-header" onClick={toggle}>
        <span className="toggle-icon">{open ? '▼' : '▶'}</span>
        {name !== undefined && <span className="json-key">{String(name)}</span>}
        {isArray && <span className="json-type"> [ {data.length} ]</span>}
      </div>
      {open && (
        <div className="json-node-children">
          {childKeys.map((ck: any) => (
            <CollapsibleNode
              key={ck}
              name={isArray ? ck : ck}
              data={isArray ? data[ck] : data[ck]}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CollapsibleJson: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="collapsible-json-viewer">
      <CollapsibleNode data={data} depth={0} />
    </div>
  );
};

export default CollapsibleJson; 