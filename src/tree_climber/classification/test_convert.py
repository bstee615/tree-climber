from tree_climber.classification.helper_parser import analyze_source_code
from tree_climber.cli.cpg import CPG
import json

source_code = """
func(o *transportObject) error {
                buffered := len(o.msg) + buf.Len()




                if !timer.Stop() {


                        select {
                        case <-timer.C:
                        default:
                        }
                }
                delay := time.Until(o.arrivalTime)
                if delay >= 0 {
                        timer.Reset(delay)
                } else {
                        timer.Reset(0)
                }

                if buffered >= bufsize {
                        select {
                        case <-timer.C:
                        case <-s.reset:
                                select {
                                case s.reset <- struct{}{}:
                                default:
                                }
                                return network.ErrReset
                        }
                        if err := drainBuf(); err != nil {
                                return err
                        }

                        _, err := s.write.Write(o.msg)
                        if err != nil {
                                return err
                        }
                } else {
                        buf.Write(o.msg)
                }
                return nil
        }
}
"""

def main():
    cpg = analyze_source_code(source_code, language="go")
    data = cpg.save_json()
    new_cpg = CPG.load_json(data)
    with open("output_cpg_new_go.json", "w", encoding="utf-8") as f:
        json.dump(new_cpg.to_dict(), f, indent=2)

if __name__ == "__main__":
    main()